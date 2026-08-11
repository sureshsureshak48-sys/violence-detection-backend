package com.example.violencedetectionsystem;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/dashboard")
public class DashboardController {

    @Autowired
    private CameraRepository cameraRepository;

    @Autowired
    private IncidentRepository incidentRepository;

    @Autowired
    private AlertRepository alertRepository;

    @GetMapping("/stats")
    public Map<String, Long> getStats() {

        Map<String, Long> stats = new HashMap<>();

        stats.put("totalCameras", cameraRepository.count());
        stats.put("totalIncidents", incidentRepository.count());
        stats.put("totalAlerts", alertRepository.count());

        return stats;
    }
}
