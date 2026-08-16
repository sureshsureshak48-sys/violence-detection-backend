package com.example.violencedetectionsystem;

import com.google.auth.oauth2.GoogleCredentials;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import jakarta.annotation.PostConstruct;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import java.io.InputStream;
import java.io.IOException;

@Component
public class FirebaseConfig {

    @PostConstruct
    public void initialize() {
        try {
            // Loads serviceAccountKey.json relative to classpath (works inside D:\IdeaProjects\violence-detection-system)
            ClassPathResource resource = new ClassPathResource("serviceAccountKey.json");
            InputStream serviceAccount = resource.getInputStream();

            FirebaseOptions options = FirebaseOptions.builder()
                    .setCredentials(GoogleCredentials.fromStream(serviceAccount))
                    .build();

            if (FirebaseApp.getApps().isEmpty()) {
                FirebaseApp.initializeApp(options);
                System.out.println("Firebase initialized successfully");
            }

        } catch (IOException e) {
            System.out.println("Firebase initialization failed: " + e.getMessage());
        }
    }
}