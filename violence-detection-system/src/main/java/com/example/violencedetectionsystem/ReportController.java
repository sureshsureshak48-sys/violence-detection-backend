package com.example.violencedetectionsystem;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/reports")
public class ReportController {

    @Autowired
    private ReportRepository reportRepository;

    @Autowired
    private IncidentRepository incidentRepository;

    @Autowired
    private CameraRepository cameraRepository;

    @GetMapping
    public List<Report> getAllReports() {
        return reportRepository.findAll();
    }

    @GetMapping("/stats")
    public java.util.Map<String, Object> getSystemStats() {
        java.util.Map<String, Object> stats = new java.util.HashMap<>();

        List<Incident> incidents = incidentRepository.findAll();
        List<Camera> cameras = cameraRepository.findAll();

        long totalIncidents = incidents.size();
        long pending = incidents.stream().filter(i -> i.getStatus() == Incident.IncidentStatus.PENDING).count();
        long approved = incidents.stream().filter(i -> i.getStatus() == Incident.IncidentStatus.APPROVED).count();
        long rejected = incidents.stream().filter(i -> i.getStatus() == Incident.IncidentStatus.REJECTED).count();

        long totalCameras = cameras.size();
        long activeCameras = cameras.stream().filter(c -> "ACTIVE".equalsIgnoreCase(c.getStatus()) || "Active".equalsIgnoreCase(c.getStatus())).count();

        double averageConfidence = incidents.stream()
                .mapToDouble(Incident::getConfidence)
                .average()
                .orElse(0.0);

        java.util.Map<String, Long> typeCounts = new java.util.HashMap<>();
        for (Incident i : incidents) {
            String type = i.getIncidentType();
            if (type != null) {
                typeCounts.put(type, typeCounts.getOrDefault(type, 0L) + 1);
            }
        }

        stats.put("totalIncidents", totalIncidents);
        stats.put("pendingIncidents", pending);
        stats.put("approvedIncidents", approved);
        stats.put("rejectedIncidents", rejected);
        stats.put("totalCameras", totalCameras);
        stats.put("activeCameras", activeCameras);
        stats.put("averageConfidence", Math.round(averageConfidence * 10.0) / 10.0);
        stats.put("incidentsByType", typeCounts);

        return stats;
    }
}
