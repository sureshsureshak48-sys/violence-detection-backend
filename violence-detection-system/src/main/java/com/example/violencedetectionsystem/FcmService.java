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

    public void sendToAllUsers(String title, String body) {
        List<UserFcmToken> tokens = tokenRepository.findAll();
        for (UserFcmToken t : tokens) {
            sendToToken(t.getFcmToken(), title, body);
        }
    }

    public void sendToToken(String token, String title, String body) {
        try {
            Message message = Message.builder()
                    .setToken(token)
                    .setNotification(
                            Notification.builder()
                                    .setTitle(title)
                                    .setBody(body)
                                    .build()
                    )
                    .build();

            String response = FirebaseMessaging.getInstance().send(message);
            System.out.println("FCM sent: " + response);

        } catch (Exception e) {
            System.out.println("FCM send failed: " + e.getMessage());
        }
    }
}