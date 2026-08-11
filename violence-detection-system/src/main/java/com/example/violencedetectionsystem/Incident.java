package com.example.violencedetectionsystem;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "incidents")
@Getter
@Setter
public class Incident {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    private IncidentStatus status;

    private String incidentType;

    private Double confidence;

    private String evidencePath;

    private Boolean verified = false;

    private String description;

    private String audioResult;

    public enum IncidentStatus {

        PENDING,
        APPROVED,
        REJECTED

    }
}
