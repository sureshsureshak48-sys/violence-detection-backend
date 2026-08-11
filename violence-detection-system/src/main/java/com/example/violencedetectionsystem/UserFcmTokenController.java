package com.example.violencedetectionsystem;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/fcm")
public class UserFcmTokenController {

    @Autowired
    private UserFcmTokenRepository repository;

    @PostMapping("/save")
    public UserFcmToken saveToken(
            @RequestBody UserFcmToken token) {

        return repository
                .findByFcmToken(
                        token.getFcmToken()
                )
                .orElseGet(() ->
                        repository.save(token)
                );
    }
}