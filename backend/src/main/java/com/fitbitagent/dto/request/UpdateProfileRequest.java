package com.fitbitagent.dto.request;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Past;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;

@Getter
@NoArgsConstructor
public class UpdateProfileRequest {

    @Size(max = 100)
    private String displayName;

    @Pattern(regexp = "MALE|FEMALE|NA", message = "gender must be MALE, FEMALE, or NA")
    private String gender;

    @DecimalMin(value = "50.0", message = "heightCm must be at least 50")
    @DecimalMax(value = "300.0", message = "heightCm must be at most 300")
    private BigDecimal heightCm;

    @Past(message = "dateOfBirth must be a past date")
    private LocalDate dateOfBirth;

    @Pattern(regexp = "sedentary|lightly_active|moderately_active|very_active|extra_active",
             message = "activityLevel must be one of: sedentary, lightly_active, moderately_active, very_active, extra_active")
    private String activityLevel;
}
