package com.fitbitagent.client.fitbit;

import java.util.Map;

import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import com.fitbitagent.config.FitbitConfig;
import com.fitbitagent.exception.FitbitApiException;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Component
@RequiredArgsConstructor
@Slf4j
public class FitbitOAuthClient {
    
    private final FitbitConfig fitbitConfig;
    private final WebClient webClient;

    public Map<String, Object> exchangeCodeForToken(String code) {
        MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
        body.add("grant_type", "authorization_code");
        body.add("code", code);
        body.add("redirect_uri", fitbitConfig.getRedirectUri());

        return callTokenEndpoint(body);
    }

    public Map<String, Object> refreshToken(String refreshToken) {
        MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
        body.add("grant_type", "refresh_token");
        body.add("refresh_token", refreshToken);

        return callTokenEndpoint(body);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> callTokenEndpoint(MultiValueMap<String, String> body) {
        try {
            return webClient.post()
                    .uri(fitbitConfig.getTokenUri())
                    .headers(headers -> headers.setBasicAuth(
                        fitbitConfig.getClientId(),
                        fitbitConfig.getClientSecret()))
                    .body(BodyInserters.fromFormData(body))
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();
        } catch (Exception e) {
            log.error("Failed to call Fitbit token endpoint", e);
            throw new FitbitApiException("Failed to obtain token from Fitbit", e);
        }
    }
}
