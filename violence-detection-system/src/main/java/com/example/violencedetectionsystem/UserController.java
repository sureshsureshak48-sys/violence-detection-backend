package com.example.violencedetectionsystem;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
public class UserController {

    @Autowired
    private UserRepository userRepository;

    @GetMapping("/users")
    public List<User> getAllUsers() {
        return userRepository.findAll();
    }
    @PostMapping("/register")
    public String registerUser(
            @RequestBody User user) {

        if (userRepository.findByEmail(
                user.getEmail()) != null) {

            return "EMAIL_EXISTS";
        }

        if (userRepository.findByUsername(
                user.getUsername()) != null) {

            return "USERNAME_EXISTS";
        }

        if (userRepository.findByMobile(
                user.getMobile()) != null) {

            return "MOBILE_EXISTS";
        }

        userRepository.save(user);

        return "REGISTER_SUCCESS";
    }
}
