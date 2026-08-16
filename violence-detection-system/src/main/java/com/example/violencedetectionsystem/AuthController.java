package com.example.violencedetectionsystem;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/auth")
public class AuthController {

    @Autowired
    private UserRepository userRepository;

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody LoginRequest request) {

        Map<String, Object> response = new HashMap<>();

        for (User user : userRepository.findAll()) {

            if (user.getUsername().equals(request.getUsername())
                    && user.getPassword().equals(request.getPassword())) {

                response.put("status", "Login Success");
                response.put("userId", user.getId());
                response.put("role", user.getRole() != null ? user.getRole() : "USER");
                return response;
            }
        }

        response.put("status", "Invalid Username or Password");
        return response;
    }
}