package com.example.violencedetectionsystem;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/evidence")
public class EvidenceController {

    @Autowired
    private EvidenceRepository evidenceRepository;

    @GetMapping
    public List<Evidence> getAllEvidence() {

        return evidenceRepository.findAll();
    }

    @GetMapping("/incident/{incidentId}")
    public List<Evidence> getEvidenceByIncident(@PathVariable Long incidentId) {
        return evidenceRepository.findByIncidentId(incidentId);
    }
    
    @DeleteMapping("/{id}")
    public String deleteEvidence(@PathVariable Long id) {
        evidenceRepository.deleteById(id);
        return "Evidence deleted";
    }
}