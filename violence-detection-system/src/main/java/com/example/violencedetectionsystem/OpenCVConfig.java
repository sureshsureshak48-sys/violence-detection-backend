package com.example.violencedetectionsystem;

import jakarta.annotation.PostConstruct;
import nu.pattern.OpenCV;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

@Configuration
public class OpenCVConfig {

    @PostConstruct
    public void init() {
        OpenCV.loadLocally();
        System.out.println("OpenCV Loaded");
    }
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
