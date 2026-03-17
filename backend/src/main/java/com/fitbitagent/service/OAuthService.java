package com.fitbitagent.service;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;

import com.fitbitagent.domain.entity.OAuthToken;
import com.fitbitagent.domain.entity.User;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.util.UriComponentsBuilder;

import com.fitbitagent.client.fitbit.FitbitOAuthClient;
import com.fitbitagent.config.FitbitConfig;
import com.fitbitagent.repository.OAuthTokenMapper;
import com.fitbitagent.repository.UserMapper;

import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Service
@RequiredArgsConstructor
@Slf4j
public class OAuthService {

    private final FitbitConfig fitbitConfig;
    private final FitbitOAuthClient fitbitOAuthClient;
    private final UserMapper userMapper;
    private final OAuthTokenMapper oAuthTokenMapper;
    private final TokenEncryptionService tokenEncryptionService;
    private final UserService userService;

    public String buildAuthorizationUrl(String state) {
        return UriComponentsBuilder.fromHttpUrl(fitbitConfig.getAuthorizationUri())
                .queryParam("response_type", "code")
                .queryParam("client_id", fitbitConfig.getClientId())
                .queryParam("redirect_uri", fitbitConfig.getRedirectUri())
                .queryParam("scope", fitbitConfig.getScope())
                .queryParam("state", state)
                .toUriString();
    }

    @Transactional
    public User handleCallback(String code, HttpSession session) {
        Map<String, Object> tokenResponse = fitbitOAuthClient.exchangeCodeForToken(code);

        String accessToken = (String) tokenResponse.get("access_token");
        String refreshToken = (String) tokenResponse.get("refresh_token");
        Integer expiresIn = (Integer) tokenResponse.get("expires_in");
        String userId = (String) tokenResponse.get("user_id");
        String scope = (String) tokenResponse.get("scope");

        boolean[] isNewUser = {false};
        User user = userMapper.findByFitbitUserId(userId)
                .orElseGet(() -> {
                    isNewUser[0] = true;
                    User newUser = User.builder()
                            .fitbitUserId(userId)
                            .build();
                    userMapper.insert(newUser);
                    return newUser;
                });

        String encryptedAccessToken = tokenEncryptionService.encrypt(accessToken);
        String encryptedRefreshToken = tokenEncryptionService.encrypt(refreshToken);
        LocalDateTime expiresAt = LocalDateTime.now().plusSeconds(expiresIn);

        oAuthTokenMapper.findByUserId(user.getId())
                .ifPresentOrElse(
                    token -> {
                        token.updateTokens(encryptedAccessToken, encryptedRefreshToken, expiresAt);
                        oAuthTokenMapper.update(token);
                    },
                    () -> oAuthTokenMapper.insert(OAuthToken.builder()
                            .userId(user.getId())
                            .accessToken(encryptedAccessToken)
                            .refreshToken(encryptedRefreshToken)
                            .expiresAt(expiresAt)
                            .scope(scope)
                            .build())
                );

        session.setAttribute("userId", user.getId());

        if (isNewUser[0]) {
            try {
                userService.fetchAndSaveProfileFromFitbit(user.getId(), accessToken);
            } catch (Exception e) {
                log.warn("Failed to fetch Fitbit profile on first login for userId={}. Profile can be synced later.", user.getId(), e);
            }
        }

        return user;
    }

    @Transactional
    public void refreshToken(UUID userId) {
        OAuthToken token = oAuthTokenMapper.findByUserId(userId)
                .orElseThrow(() -> new RuntimeException("Token not found for user: " + userId));

        String decryptedRefreshToken = tokenEncryptionService.decrypt(token.getRefreshToken());
        Map<String, Object> tokenResponse = fitbitOAuthClient.refreshToken(decryptedRefreshToken);

        String newAccessToken = (String) tokenResponse.get("access_token");
        String newRefreshToken = (String) tokenResponse.get("refresh_token");
        Integer expiresIn = (Integer) tokenResponse.get("expires_in");

        token.updateTokens(
                tokenEncryptionService.encrypt(newAccessToken),
                tokenEncryptionService.encrypt(newRefreshToken),
                LocalDateTime.now().plusSeconds(expiresIn)
        );
        oAuthTokenMapper.update(token);
    }

}
