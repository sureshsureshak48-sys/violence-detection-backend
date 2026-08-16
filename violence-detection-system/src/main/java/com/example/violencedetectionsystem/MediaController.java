package com.example.violencedetectionsystem;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.client.RestTemplate;

import java.io.File;
import java.io.IOException;

import org.springframework.core.io.FileSystemResource;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@RestController
@RequestMapping("/media")
public class MediaController {

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private IncidentRepository incidentRepository;

    @Autowired
    private EvidenceRepository evidenceRepository;

    @PostMapping("/upload")
    public String uploadFile(
            @RequestParam("file") MultipartFile file)
            throws IOException {

        String uploadDir =
                System.getProperty("user.dir") + "/uploads/";

        File dir = new File(uploadDir);

        if (!dir.exists()) {
            dir.mkdirs();
        }

        String filePath =
                uploadDir + file.getOriginalFilename();

        file.transferTo(new File(filePath));

        FileSystemResource resource =
                new FileSystemResource(filePath);

        MultiValueMap<String, Object> body =
                new LinkedMultiValueMap<>();

        body.add("file", resource);

        HttpHeaders headers = new HttpHeaders();

        headers.setContentType(
                MediaType.MULTIPART_FORM_DATA
        );

        HttpEntity<MultiValueMap<String, Object>>
                requestEntity =
                new HttpEntity<>(body, headers);
        String contentType = file.getContentType();
        String filename = file.getOriginalFilename().toLowerCase();

        String endpoint;

        if (filename.endsWith(".mp4")
                || filename.endsWith(".mov")
                || filename.endsWith(".avi")
                || filename.endsWith(".webm")
                || filename.endsWith(".mkv")
                || filename.endsWith(".flv")
                || filename.endsWith(".wmv")) {

            endpoint = "http://127.0.0.1:5000/detect-video";

        } else {

            endpoint = "http://127.0.0.1:5000/detect";

        }
        System.out.println("FILE = " + filename);
        System.out.println("ENDPOINT = " + endpoint);

        ResponseEntity<String> response =
                restTemplate.postForEntity(
                        endpoint,
                        requestEntity,
                        String.class
                );

        System.out.println(response.getBody());

        ObjectMapper mapper = new ObjectMapper();

        JsonNode json =
                mapper.readTree(
                        response.getBody()
                );

        boolean violence =
                json.path("violence")
                        .asBoolean(false);

        if (violence) {

            Incident incident =
                    new Incident();

            incident.setIncidentType(
                    json.path(
                            "overall_violence_type"
                    ).asText("Violence")
            );

            incident.setConfidence(
                    json.path(
                            "confidence").asDouble(0));

            incident.setAudioResult(
                    json.path(
                            "audio_result"
                    ).asText("Unknown")
            );

            String coreContent = json.path("core_content").asText("A physical altercation / violence detected.");
            StringBuilder objStr = new StringBuilder();
            if (json.has("objects") && !json.get("objects").isEmpty()) {
                objStr.append(" | Objects: ");
                json.get("objects").fields().forEachRemaining(entry -> {
                    objStr.append(entry.getKey()).append("(").append(entry.getValue().asInt()).append(") ");
                });
            }

            incident.setDescription(coreContent + objStr.toString());

            incident.setEvidencePath(filePath);

            incident.setStatus(Incident.IncidentStatus.PENDING);

            incidentRepository.save(incident);

            // Save annotated image evidence
            String annotatedPath = json.path("annotated_image_path").asText("");
            if (!annotatedPath.isEmpty()) {
                Evidence imgEvidence = new Evidence();
                imgEvidence.setIncidentId(incident.getId());
                imgEvidence.setFilePath(annotatedPath);
                imgEvidence.setFileType("IMAGE");
                evidenceRepository.save(imgEvidence);
            }

            // Save video clip evidence
            String videoClipPath = json.path("video_clip_path").asText("");
            if (!videoClipPath.isEmpty()) {
                Evidence vidEvidence = new Evidence();
                vidEvidence.setIncidentId(incident.getId());
                vidEvidence.setFilePath(videoClipPath);
                vidEvidence.setFileType("VIDEO");
                evidenceRepository.save(vidEvidence);
            }

            // Save audio clip evidence
            String audioClipPath = json.path("audio_clip_path").asText("");
            if (!audioClipPath.isEmpty()) {
                Evidence audEvidence = new Evidence();
                audEvidence.setIncidentId(incident.getId());
                audEvidence.setFilePath(audioClipPath);
                audEvidence.setFileType("AUDIO");
                evidenceRepository.save(audEvidence);
            }
        }

        return response.getBody();
    }
}