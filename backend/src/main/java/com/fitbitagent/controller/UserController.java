package com.fitbitagent.controller;

import com.fitbitagent.dto.request.UpdateProfileRequest;
import com.fitbitagent.dto.response.UserProfileResponse;
import com.fitbitagent.service.UserService;
import jakarta.servlet.http.HttpSession;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
@Slf4j
public class UserController {

    private final UserService userService;

    @GetMapping("/me")
    public ResponseEntity<UserProfileResponse> getProfile(HttpSession session) {
        UUID userId = (UUID) session.getAttribute("userId");
        UserProfileResponse profile = userService.getUserProfile(userId);
        return ResponseEntity.ok(profile);
    }

    @PutMapping("/me")
    public ResponseEntity<UserProfileResponse> updateProfile(
            @Valid @RequestBody UpdateProfileRequest request,
            HttpSession session) {
        UUID userId = (UUID) session.getAttribute("userId");
        UserProfileResponse profile = userService.updateUserProfile(userId, request);
        return ResponseEntity.ok(profile);
    }
}
