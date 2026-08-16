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

    @GetMapping("/users/{id}")
    public User getUserById(@PathVariable Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));
    }

    @PutMapping("/users/{id}")
    public User updateProfile(@PathVariable Long id, @RequestBody User updatedUser) {
        return userRepository.findById(id).map(user -> {
            user.setFullName(updatedUser.getFullName());
            user.setEmail(updatedUser.getEmail());
            user.setMobile(updatedUser.getMobile());
            return userRepository.save(user);
        }).orElseThrow(() -> new RuntimeException("User not found"));
    }

    @PutMapping("/users/{id}/password")
    public String updatePassword(@PathVariable Long id, @RequestBody java.util.Map<String, String> payload) {
        String newPassword = payload.get("password");
        User user = userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));
        user.setPassword(newPassword);
        userRepository.save(user);
        return "PASSWORD_UPDATE_SUCCESS";
    }
}
