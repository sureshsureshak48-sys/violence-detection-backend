package com.example.violencedetectionsystem;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface IncidentRepository
        extends JpaRepository<Incident, Long> {

    List<Incident> findByStatus(
            Incident.IncidentStatus status
    );
    List<Incident> findByVerifiedTrue();
}