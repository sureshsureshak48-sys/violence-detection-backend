package com.example.violencedetectionsystem;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/incidents")
public class IncidentController {

    @Autowired
    private CameraRepository cameraRepository;

    @Autowired
    private AiDetectionService aiDetectionService;

    @Autowired
    private IncidentRepository incidentRepository;

    @GetMapping
    public List<Incident> getAllIncidents() {
        return incidentRepository.findAll();
    }

    @PostMapping
    public Incident addIncident(
            @RequestBody Incident incident) {

        return incidentRepository.save(incident);
    }

    @PutMapping("/verify/{id}")
    public Incident verifyIncident(
            @PathVariable Long id) {

        Incident incident =
                incidentRepository
                        .findById(id)
                        .orElseThrow();

        incident.setVerified(true);

        return incidentRepository.save(
                incident
        );
    }
    @GetMapping("/verified")
    public List<Incident> verifiedIncidents() {

        return incidentRepository
                .findByVerifiedTrue();
    }
    @PostMapping("/analyzeCamera/{cameraId}")
    public ResponseEntity<?> analyzeCamera(@PathVariable Long cameraId) {

        Camera camera = cameraRepository.findById(cameraId)
                .orElseThrow(() -> new RuntimeException("Camera not found"));

        Map<String, Object> result =
                aiDetectionService.analyzeRtsp(camera.getRtspUrl());

        return ResponseEntity.ok(result);
    }

    @GetMapping("/recent")
    public List<Incident> getRecentIncidents() {

        return incidentRepository.findAll();
    }
}