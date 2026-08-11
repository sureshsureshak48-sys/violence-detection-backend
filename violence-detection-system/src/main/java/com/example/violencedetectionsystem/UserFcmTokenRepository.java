package com.example.violencedetectionsystem;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface UserFcmTokenRepository
        extends JpaRepository<UserFcmToken, Long> {

    Optional<UserFcmToken>
    findByFcmToken(String fcmToken);

}