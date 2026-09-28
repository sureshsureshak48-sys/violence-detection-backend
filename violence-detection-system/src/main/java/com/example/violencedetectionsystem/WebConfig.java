package com.example.violencedetectionsystem;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import java.nio.file.Paths;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        String baseDir = System.getProperty("user.dir");

        String datasetUri = new java.io.File("dataset").toURI().toString();
        if (!datasetUri.endsWith("/")) datasetUri += "/";
        registry.addResourceHandler("/dataset/**")
                .addResourceLocations(datasetUri);

        String evidenceUri = new java.io.File("ai-service/evidence").toURI().toString();
        if (!evidenceUri.endsWith("/")) evidenceUri += "/";
        System.out.println("SERVING EVIDENCE FROM: " + evidenceUri);
        registry.addResourceHandler("/evidence/**")
                .addResourceLocations(evidenceUri);

        String uploadsUri = new java.io.File("ai-service/uploads").toURI().toString();
        if (!uploadsUri.endsWith("/")) uploadsUri += "/";
        registry.addResourceHandler("/uploads/**")
                .addResourceLocations(uploadsUri);
    }
}
