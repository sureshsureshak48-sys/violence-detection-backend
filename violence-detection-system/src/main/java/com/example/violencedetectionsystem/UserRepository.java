package com.example.violencedetectionsystem;

import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, Long> {

    User findByUsernameAndPassword(
            String username,
            String password
    );

    User findByEmail(String email);

    User findByUsername(String username);

    User findByMobile(String mobile);
}