package com.example.violencedetectionsystem;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import java.nio.file.Paths;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // Exposes http://localhost:8080/dataset/... to your Flutter frontend
        String datasetUri = Paths.get("dataset").toUri().toString();
        registry.addResourceHandler("/dataset/**")
                .addResourceLocations(datasetUri);

        // Serve evidence files (annotated images, video clips, audio clips)
        String evidenceUri = Paths.get("ai-service", "evidence").toUri().toString();
        registry.addResourceHandler("/evidence/**")
                .addResourceLocations(evidenceUri);

        // Serve uploaded files
        String uploadsUri = Paths.get("ai-service", "uploads").toUri().toString();
        registry.addResourceHandler("/uploads/**")
                .addResourceLocations(uploadsUri);
    }
}
