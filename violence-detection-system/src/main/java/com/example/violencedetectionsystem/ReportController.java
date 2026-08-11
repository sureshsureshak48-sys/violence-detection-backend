package com.example.violencedetectionsystem;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/reports")
public class ReportController {

    @Autowired
    private ReportRepository reportRepository;

    @GetMapping
    public List<Report> getAllReports() {
        return reportRepository.findAll();
    }
}
