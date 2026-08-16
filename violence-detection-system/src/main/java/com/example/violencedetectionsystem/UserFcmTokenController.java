package com.example.violencedetectionsystem;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/fcm")
public class UserFcmTokenController {

    @Autowired
    private UserFcmTokenRepository repository;

    @PostMapping("/save")
    public UserFcmToken saveToken(@RequestBody UserFcmToken token) {
        if (token.getFcmToken() == null || token.getFcmToken().trim().isEmpty()) {
            return token;
        }

        return repository.findByFcmToken(token.getFcmToken().trim())
                .map(existing -> {
                    existing.setUserId(token.getUserId());
                    return repository.save(existing);
                })
                .orElseGet(() -> repository.save(token));
    }
}