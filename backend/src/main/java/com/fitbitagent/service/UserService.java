package com.fitbitagent.service;

import com.fitbitagent.client.fitbit.dto.FitbitProfileResponse;
import com.fitbitagent.domain.entity.User;
import com.fitbitagent.dto.request.UpdateProfileRequest;
import com.fitbitagent.dto.response.UserProfileResponse;
import com.fitbitagent.exception.FitbitApiException;
import com.fitbitagent.exception.ResourceNotFoundException;
import com.fitbitagent.repository.UserMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserMapper userMapper;
    private final WebClient webClient;

    @Transactional(readOnly = true)
    public UserProfileResponse getUserProfile(UUID userId) {
        User user = userMapper.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));
        return UserProfileResponse.from(user);
    }

    @Transactional
    public UserProfileResponse updateUserProfile(UUID userId, UpdateProfileRequest request) {
        User user = userMapper.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));

        user.updateProfile(
                request.getDisplayName(),
                request.getGender(),
                request.getHeightCm(),
                request.getDateOfBirth(),
                request.getActivityLevel()
        );
        userMapper.update(user);

        log.info("User profile updated: userId={}", userId);
        return UserProfileResponse.from(user);
    }

    @Transactional
    public void fetchAndSaveProfileFromFitbit(UUID userId, String accessToken) {
        try {
            FitbitProfileResponse response = webClient.get()
                    .uri("https://api.fitbit.com/1/user/-/profile.json")
                    .headers(headers -> headers.setBearerAuth(accessToken))
                    .retrieve()
                    .bodyToMono(FitbitProfileResponse.class)
                    .block();

            if (response == null || response.getUser() == null) {
                log.warn("Empty profile response from Fitbit for userId={}", userId);
                return;
            }

            FitbitProfileResponse.UserData profile = response.getUser();

            User user = userMapper.findById(userId)
                    .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));

            BigDecimal heightCm = profile.getHeight();
            LocalDate dateOfBirth = null;
            if (profile.getDateOfBirth() != null && !profile.getDateOfBirth().isBlank()) {
                dateOfBirth = LocalDate.parse(profile.getDateOfBirth());
            }

            user.updateProfile(
                    profile.getDisplayName(),
                    profile.getGender(),
                    heightCm,
                    dateOfBirth,
                    null
            );
            userMapper.update(user);

            log.info("Fitbit profile fetched and saved for userId={}", userId);
        } catch (FitbitApiException e) {
            throw e;
        } catch (Exception e) {
            log.error("Failed to fetch profile from Fitbit for userId={}", userId, e);
            throw new FitbitApiException("Failed to fetch Fitbit user profile", e);
        }
    }
}
