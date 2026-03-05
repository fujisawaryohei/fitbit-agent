package com.fitbitagent.config;

import lombok.Getter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
@Getter
public class FitbitConfig {
    @Value("${fitbit.client-id}")
    private String clientId;

    @Value("${fitbit.client-secret}")
    private String clientSecret;

    @Value("${fitbit.redirect-uri}")
    private String redirectUri;

    @Value("${fitbit.authorization-uri:https://www.fitbit.com/oauth2/authorize}")
    private String authorizationUri;

    @Value("${fitbit.token-uri:https://api.fitbit.com/oauth2/token}")
    private String tokenUri;

    @Value("${fitbit.api-base-url:https://api.fitbit.com}")
    private String apiBaseUrl;

    @Value("${fitbit.scope:activity heartrate location nutrition profile settings sleep social weight}")
    private String scope;   
}
