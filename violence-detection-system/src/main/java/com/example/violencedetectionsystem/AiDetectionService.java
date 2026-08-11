package com.example.violencedetectionsystem;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@Service
public class AiDetectionService {

    @Value("${ai.server.url:http://localhost:5000}")
    private String aiServerUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    public Map<String, Object> analyzeRtsp(String rtspUrl) {

        String url = aiServerUrl + "/analyze";

        Map<String, String> request = new HashMap<>();
        request.put("rtspUrl", rtspUrl);

        return restTemplate.postForObject(
                url,
                request,
                Map.class
        );
    }
}