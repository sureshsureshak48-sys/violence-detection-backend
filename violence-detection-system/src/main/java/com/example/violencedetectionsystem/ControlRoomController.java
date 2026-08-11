package com.example.violencedetectionsystem;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.MediaType;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/control-room")
public class ControlRoomController {

    @Autowired
    private IncidentRepository incidentRepository;

    @Autowired
    private EvidenceRepository evidenceRepository;

    @Autowired
    private AlertRepository alertRepository;

    @Autowired
    private FcmService fcmService;

    @GetMapping(
            value="/pending",
            produces =
                    MediaType.APPLICATION_JSON_VALUE
    )
    public List<Incident> getPendingIncidents() {

        return incidentRepository.findByStatus(
                Incident.IncidentStatus.PENDING
        );
    }

    @PutMapping("/approve/{id}")
    public String approveIncident(
            @PathVariable Long id,
            @RequestBody(required = false) Map<String, String> body) {

        Incident incident = incidentRepository.findById(id).orElse(null);

        if (incident == null) {
            return "Incident Not Found";
        }

        if (incident.getStatus()
                == Incident.IncidentStatus.APPROVED) {

            return "Already Approved";
        }

        String finalType = (body != null && body.get("violenceType") != null)
                ? body.get("violenceType")
                : incident.getIncidentType();

        incident.setStatus(Incident.IncidentStatus.APPROVED);
        incident.setVerified(true);
        incident.setIncidentType(finalType);
        incidentRepository.save(incident);

        Alert alert = new Alert();
        alert.setMessage(finalType + " detected");
        alert.setAlertTime(java.time.LocalDateTime.now().toString());
        alert.setViolenceType(finalType);
        alert.setConfidence(incident.getConfidence());
        alert.setIncidentId(incident.getId());

        alertRepository.save(alert);

        if (incident.getEvidencePath() != null && !incident.getEvidencePath().isEmpty()) {
            Evidence evidence = new Evidence();
            evidence.setIncidentId(incident.getId());
            evidence.setFilePath(incident.getEvidencePath());

            String path = incident.getEvidencePath().toLowerCase();
            evidence.setFileType(path.endsWith(".mp4") ? "VIDEO" : "IMAGE");

            evidenceRepository.save(evidence);
        }

        fcmService.sendToAllUsers(
                "Violence Detected",
                finalType + " detected with " + incident.getConfidence() + "% confidence"
        );

        return "Incident Approved";
    }

    @PutMapping("/reject/{id}")
    public String rejectIncident(
            @PathVariable Long id
    ) {

        Incident incident =
                incidentRepository.findById(id)
                        .orElse(null);

        if (incident == null) {
            return "Incident Not Found";
        }

        incident.setStatus(
                Incident.IncidentStatus.REJECTED
        );

        incidentRepository.save(incident);

        return "Incident Rejected";
    }
}