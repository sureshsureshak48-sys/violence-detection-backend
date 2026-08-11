package com.example.violencedetectionsystem;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.client.RestTemplate;

import java.io.File;
import java.io.IOException;

import org.springframework.core.io.FileSystemResource;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@RestController
@RequestMapping("/media")
public class MediaController {

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private IncidentRepository incidentRepository;

    @Autowired
    private EvidenceRepository evidenceRepository;

    @PostMapping("/upload")
    public String uploadFile(
            @RequestParam("file") MultipartFile file)
            throws IOException {

        String uploadDir =
                System.getProperty("user.dir") + "/uploads/";

        File dir = new File(uploadDir);

        if (!dir.exists()) {
            dir.mkdirs();
        }

        String filePath =
                uploadDir + file.getOriginalFilename();

        file.transferTo(new File(filePath));

        FileSystemResource resource =
                new FileSystemResource(filePath);

        MultiValueMap<String, Object> body =
                new LinkedMultiValueMap<>();

        body.add("file", resource);

        HttpHeaders headers = new HttpHeaders();

        headers.setContentType(
                MediaType.MULTIPART_FORM_DATA
        );

        HttpEntity<MultiValueMap<String, Object>>
                requestEntity =
                new HttpEntity<>(body, headers);
        String contentType = file.getContentType();
        String filename = file.getOriginalFilename().toLowerCase();

        String endpoint;

        if (filename.endsWith(".mp4")
                || filename.endsWith(".mov")
                || filename.endsWith(".avi")
                || filename.endsWith(".webm")
                || filename.endsWith(".mkv")
                || filename.endsWith(".flv")
                || filename.endsWith(".wmv")) {

            endpoint = "http://127.0.0.1:5000/detect-video";

        } else {

            endpoint = "http://127.0.0.1:5000/detect";

        }
        System.out.println("FILE = " + filename);
        System.out.println("ENDPOINT = " + endpoint);

        ResponseEntity<String> response =
                restTemplate.postForEntity(
                        endpoint,
                        requestEntity,
                        String.class
                );

        System.out.println(response.getBody());

        ObjectMapper mapper = new ObjectMapper();

        JsonNode json =
                mapper.readTree(
                        response.getBody()
                );

        boolean violence =
                json.path("violence")
                        .asBoolean(false);

        if (violence) {

            Incident incident =
                    new Incident();

            incident.setIncidentType(
                    json.path(
                            "overall_violence_type"
                    ).asText("Violence")
            );

            incident.setConfidence(
                    json.path(
                            "confidence").asDouble(0));

            incident.setAudioResult(
                    json.path(
                            "audio_result"
                    ).asText("Unknown")
            );

            incident.setEvidencePath(filePath);

            incident.setStatus(Incident.IncidentStatus.PENDING);

            incidentRepository.save(incident);

            Evidence evidence = new Evidence();

            evidence.setIncidentId(
                    incident.getId()
            );

            evidence.setFilePath(
                    filePath
            );

            evidence.setFileType(
                    filename.endsWith(".mp4")
                            ? "VIDEO"
                            : "IMAGE"
            );

            evidenceRepository.save(
                    evidence
            );
        }

        return response.getBody();
    }
}