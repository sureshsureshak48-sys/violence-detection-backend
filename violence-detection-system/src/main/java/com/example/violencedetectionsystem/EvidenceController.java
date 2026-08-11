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
}