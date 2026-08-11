package com.example.violencedetectionsystem;

import jakarta.persistence.*;

@Entity
@Table(name = "user_fcm_token")
public class UserFcmToken {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long userId;

    @Column(columnDefinition = "TEXT")
    private String fcmToken;

    public Long getId() {
        return id;
    }

    public Long getUserId() {
        return userId;
    }

    public String getFcmToken() {
        return fcmToken;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public void setFcmToken(String fcmToken) {
        this.fcmToken = fcmToken;
    }
}