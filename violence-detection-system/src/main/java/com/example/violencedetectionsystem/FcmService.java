package com.example.violencedetectionsystem;

import com.google.firebase.messaging.FirebaseMessaging;
import com.google.firebase.messaging.Message;
import com.google.firebase.messaging.Notification;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class FcmService {

    @Autowired
    private UserFcmTokenRepository tokenRepository;

    public void sendToAllUsers(String title, String body, String screen, String incidentId) {
        List<UserFcmToken> tokens = tokenRepository.findAll();
        
        // Deduplicate tokens so each physical device receives EXACTLY ONE notification per approval
        java.util.Set<String> uniqueTokens = new java.util.HashSet<>();
        for (UserFcmToken t : tokens) {
            if (t.getFcmToken() != null && !t.getFcmToken().trim().isEmpty()) {
                uniqueTokens.add(t.getFcmToken().trim());
            }
        }

        System.out.println("=== FCM BROADCAST START ===");
        System.out.println("Sending 1 notification to " + uniqueTokens.size() + " unique device(s)");

        for (String token : uniqueTokens) {
            sendToToken(token, title, body, screen, incidentId);
        }
        System.out.println("=== FCM BROADCAST END ===");
    }

    public void sendToToken(String token, String title, String body, String screen, String incidentId) {
        try {
            Message message = Message.builder()
                    .setToken(token)
                    .setNotification(
                            Notification.builder()
                                    .setTitle(title)
                                    .setBody(body)
                                    .build()
                    )
                    .putData("screen", screen != null ? screen : "")
                    .putData("incidentId", incidentId != null ? incidentId : "")
                    .build();

            String response = FirebaseMessaging.getInstance().send(message);
            System.out.println("✅ FCM sent successfully: " + response);

        } catch (Exception e) {
            System.err.println("❌ FCM send failed for token [" + token + "]: " + e.getMessage());
            e.printStackTrace();
        }
    }
}