package com.example.violencedetectionsystem;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class AIResponse {

    private String status;
    private String incidentType;
    private Double confidence;
}