package com.example.violencedetectionsystem;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "cameras")
@Getter
@Setter
public class Camera {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String cameraName;

    private String rtspUrl;

    private String status;
}