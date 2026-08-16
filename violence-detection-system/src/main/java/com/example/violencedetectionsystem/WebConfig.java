package com.example.violencedetectionsystem;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import java.io.File;
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // Absolute path to your dataset folder on D: drive
        String datasetPath = new File("dataset").getAbsolutePath();

        // Exposes http://localhost:8080/dataset/... to your Flutter frontend
        registry.addResourceHandler("/dataset/**")
                .addResourceLocations("file:" + datasetPath + "/");

        // Serve evidence files (annotated images, video clips, audio clips)
        String evidencePath = new File("ai-service/evidence").getAbsolutePath();
        registry.addResourceHandler("/evidence/**")
                .addResourceLocations("file:" + evidencePath + "/");

        // Serve uploaded files
        String uploadsPath = new File("ai-service/uploads").getAbsolutePath();
        registry.addResourceHandler("/uploads/**")
                .addResourceLocations("file:" + uploadsPath + "/");
    }
}
