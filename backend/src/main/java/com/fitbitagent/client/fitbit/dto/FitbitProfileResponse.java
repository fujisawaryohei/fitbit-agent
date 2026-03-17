package com.fitbitagent.client.fitbit.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

@Getter
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class FitbitProfileResponse {

    @JsonProperty("user")
    private UserData user;

    @Getter
    @NoArgsConstructor
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UserData {
        private String displayName;
        private String gender;
        private BigDecimal height;
        private String dateOfBirth;
        private String averageDailySteps;
    }
}
