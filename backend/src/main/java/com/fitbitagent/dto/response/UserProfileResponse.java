package com.fitbitagent.dto.response;

import com.fitbitagent.domain.entity.User;
import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Builder
public class UserProfileResponse {

    private UUID id;
    private String fitbitUserId;
    private String displayName;
    private String gender;
    private BigDecimal heightCm;
    private LocalDate dateOfBirth;
    private String activityLevel;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public static UserProfileResponse from(User user) {
        return UserProfileResponse.builder()
                .id(user.getId())
                .fitbitUserId(user.getFitbitUserId())
                .displayName(user.getDisplayName())
                .gender(user.getGender())
                .heightCm(user.getHeightCm())
                .dateOfBirth(user.getDateOfBirth())
                .activityLevel(user.getActivityLevel())
                .createdAt(user.getCreatedAt())
                .updatedAt(user.getUpdatedAt())
                .build();
    }
}
