package com.example.violencedetectionsystem;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "alerts")
@Getter
@Setter
public class Alert {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String message;

    private String alertTime;

    private String violenceType;

    private Double confidence;        // eg: 91.4

    private String cameraName;        // eg: "Camera 1"

    private Long incidentId;          // link back to the incident/evidence
}