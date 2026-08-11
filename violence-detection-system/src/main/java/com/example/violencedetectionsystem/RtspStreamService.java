package com.example.violencedetectionsystem;

import org.opencv.core.Mat;
import org.opencv.core.MatOfByte;
import org.opencv.core.Size;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.videoio.VideoCapture;
import org.opencv.videoio.VideoWriter;
import org.opencv.videoio.Videoio;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.core.io.FileSystemResource;
import java.awt.image.BufferedImage;

import javax.imageio.ImageIO;
import java.io.ByteArrayInputStream;
import java.io.File;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class RtspStreamService {

    @Autowired
    private IncidentRepository incidentRepository;

    private final RestTemplate restTemplate = new RestTemplate();

    // ~2-3 seconds of clip per analysis chunk (fps depend pannirukum)
    private static final int CLIP_FRAME_COUNT = 48;

    // idha volatile-ah vaikkurom, stopDetection() velila irundhu loop-ah nிறுthanum
    private volatile boolean running = false;

    public void startDetection(String rtspUrl) {

        running = true;

        VideoCapture cap = new VideoCapture(rtspUrl);

        if (!cap.isOpened()) {
            System.out.println("RTSP Stream Open Failed");
            return;
        }

        double fps = cap.get(Videoio.CAP_PROP_FPS);
        if (fps <= 1) {
            fps = 20;   // fallback, சில RTSP streams fps correct-ah kudukaathu
        }

        Mat frame = new Mat();
        int frameCount = 0;

        String clipPath = "uploads/rtsp_clip.mp4";
        VideoWriter writer = null;

        while (running) {

            boolean success = cap.read(frame);

            if (!success || frame.empty()) {
                System.out.println("RTSP frame read failed, stopping.");
                break;
            }

            if (writer == null) {
                Size frameSize = new Size(frame.cols(), frame.rows());
                writer = new VideoWriter(
                        clipPath,
                        VideoWriter.fourcc('m', 'p', '4', 'v'),
                        fps,
                        frameSize
                );
            }

            writer.write(frame);
            frameCount++;

            if (frameCount >= CLIP_FRAME_COUNT) {

                writer.release();
                writer = null;
                frameCount = 0;

                // namba full pipeline (YOLO + motion + audio) idha vachi analyze pannurom
                sendClipForAnalysis(clipPath);
            }
        }

        if (writer != null) {
            writer.release();
        }

        cap.release();
        System.out.println("RTSP detection stopped.");
    }

    public void stopDetection() {
        running = false;
    }

    private void sendClipForAnalysis(String clipPath) {

        FileSystemResource resource = new FileSystemResource(new File(clipPath));

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", resource);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

        try {

            // /detect (image) ku pathila /detect-video - idhu namba full weapon+motion+audio logic
            ResponseEntity<String> response = restTemplate.postForEntity(
                    "http://127.0.0.1:5000/detect-video",
                    request,
                    String.class
            );

            ObjectMapper mapper = new ObjectMapper();
            JsonNode json = mapper.readTree(response.getBody());

            boolean violence = json.path("violence").asBoolean(false);

            System.out.println("CAMERA CLIP RESULT = " + response.getBody());

            if (violence) {

                Incident incident = new Incident();

                incident.setIncidentType(
                        json.path("overall_violence_type").asText("Violence")
                );

                incident.setConfidence(
                        json.path("confidence").asDouble(0)
                );

                incident.setEvidencePath(clipPath);

                incident.setDescription(response.getBody());

                incident.setStatus(Incident.IncidentStatus.PENDING);

                incident.setVerified(false);

                incidentRepository.save(incident);

                System.out.println("INCIDENT CREATED FROM CAMERA");
            }

        } catch (Exception e) {
            System.out.println("AI ERROR = " + e.getMessage());
        }
    }

    public BufferedImage captureFrame(String rtspUrl) {

        VideoCapture capture = new VideoCapture(rtspUrl);

        Mat frame = new Mat();

        if (capture.read(frame)) {
            capture.release();
            return matToBufferedImage(frame);
        }

        capture.release();
        return null;
    }

    private BufferedImage matToBufferedImage(Mat mat) {

        MatOfByte mob = new MatOfByte();
        Imgcodecs.imencode(".jpg", mat, mob);

        byte[] bytes = mob.toArray();

        try {
            return ImageIO.read(new ByteArrayInputStream(bytes));
        } catch (Exception e) {
            return null;
        }
    }
}