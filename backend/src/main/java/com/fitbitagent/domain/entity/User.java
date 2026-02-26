package com.fitbitagent.domain.entity;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {
    private UUID id;
    private String fitbitUserId;
    private String displayName;
    private String gender;
    private BigDecimal heightCm;
    private LocalDate dateOfBirth;
    private String activityLevel;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    
    public void updateProfile(String displayName, String gender, BigDecimal heightCm, LocalDate dateOfBirth, String activityLevel) {
        this.displayName = displayName;
        this.gender = gender;
        this.heightCm = heightCm;
        this.dateOfBirth = dateOfBirth;
        this.activityLevel = activityLevel;
        this.updatedAt = LocalDateTime.now();
    }
}