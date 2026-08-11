package com.example.violencedetectionsystem;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/cameras")
public class CameraController {

    @Autowired
    private CameraRepository cameraRepository;

    @GetMapping
    public List<Camera> getAllCameras() {
        return cameraRepository.findAll();
    }
    @PostMapping
    public Camera addCamera(@RequestBody Camera camera) {
        return cameraRepository.save(camera);
    }

    @Autowired
    private RtspStreamService rtspStreamService;

    @PostMapping("/start-rtsp")
    public String startRtsp(
            @RequestParam String rtspUrl) {

        rtspStreamService.startDetection(
                rtspUrl
        );

        return "RTSP Detection Started";
    }
    @PostMapping("/startDetection/{cameraId}")
    public String startDetection(
            @PathVariable Long cameraId) {

        Camera camera =
                cameraRepository.findById(cameraId)
                        .orElseThrow();

        new Thread(() -> {
            rtspStreamService.startDetection(camera.getRtspUrl());
        }).start();

        return "Detection Started";
    }
    @PostMapping("/stopDetection")
    public String stopDetection() {
        rtspStreamService.stopDetection();
        return "Detection Stopped";
    }
}