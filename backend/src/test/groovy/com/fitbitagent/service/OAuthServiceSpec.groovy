package com.fitbitagent.service

import com.fitbitagent.client.fitbit.FitbitOAuthClient
import com.fitbitagent.config.FitbitConfig
import com.fitbitagent.domain.entity.OAuthToken
import com.fitbitagent.domain.entity.User
import com.fitbitagent.repository.OAuthTokenMapper
import com.fitbitagent.repository.UserMapper
import jakarta.servlet.http.HttpSession
import spock.lang.Specification
import spock.lang.Subject

import java.time.LocalDateTime
import java.util.Optional
import java.util.UUID

class OAuthServiceSpec extends Specification {

    // Collaborators (mocked)
    FitbitConfig            fitbitConfig            = Mock()
    FitbitOAuthClient       fitbitOAuthClient       = Mock()
    UserMapper              userMapper              = Mock()
    OAuthTokenMapper        oAuthTokenMapper        = Mock()
    TokenEncryptionService  tokenEncryptionService  = Mock()
    HttpSession             session                 = Mock()

    @Subject
    OAuthService service = new OAuthService(
            fitbitConfig,
            fitbitOAuthClient,
            userMapper,
            oAuthTokenMapper,
            tokenEncryptionService
    )

    // ─────────────────────────────────────────────────────────────────────
    // buildAuthorizationUrl
    // ─────────────────────────────────────────────────────────────────────

    def "buildAuthorizationUrl should include all required OAuth2 query parameters"() {
        given:
        fitbitConfig.getAuthorizationUri() >> "https://www.fitbit.com/oauth2/authorize"
        fitbitConfig.getClientId()         >> "test-client-id"
        fitbitConfig.getRedirectUri()      >> "http://localhost:8080/api/auth/callback"
        fitbitConfig.getScope()            >> "activity heartrate profile"

        when:
        def url = service.buildAuthorizationUrl("random-state-value")

        then:
        url.contains("response_type=code")
        url.contains("client_id=test-client-id")
        url.contains("redirect_uri=")
        url.contains("scope=")
        url.contains("state=random-state-value")
        url.startsWith("https://www.fitbit.com/oauth2/authorize")
    }

    def "buildAuthorizationUrl should embed the given state parameter"() {
        given:
        fitbitConfig.getAuthorizationUri() >> "https://www.fitbit.com/oauth2/authorize"
        fitbitConfig.getClientId()         >> "cid"
        fitbitConfig.getRedirectUri()      >> "http://localhost:8080/api/auth/callback"
        fitbitConfig.getScope()            >> "activity"

        when:
        def url = service.buildAuthorizationUrl("my-unique-state")

        then:
        url.contains("state=my-unique-state")
    }

    // ─────────────────────────────────────────────────────────────────────
    // handleCallback – new user
    // ─────────────────────────────────────────────────────────────────────

    def "handleCallback should create a new user and persist encrypted tokens when user does not exist"() {
        given:
        def fitbitUserId = "fitbit-user-123"
        def tokenResponse = [
            access_token : "raw-access-token",
            refresh_token: "raw-refresh-token",
            expires_in   : 28800,
            user_id      : fitbitUserId,
            scope        : "activity",
        ] as Map<String, Object>

        fitbitOAuthClient.exchangeCodeForToken("auth-code") >> tokenResponse
        userMapper.findByFitbitUserId(fitbitUserId)         >> Optional.empty()
        tokenEncryptionService.encrypt("raw-access-token")  >> "enc-access"
        tokenEncryptionService.encrypt("raw-refresh-token") >> "enc-refresh"
        // Use wildcard: UUID is generated inside the lambda so we cannot predict it
        oAuthTokenMapper.findByUserId(_)                    >> Optional.empty()

        when:
        def result = service.handleCallback("auth-code", session)

        then:
        1 * userMapper.insert(_ as User)
        1 * oAuthTokenMapper.insert({ OAuthToken t ->
            t.accessToken  == "enc-access" &&
            t.refreshToken == "enc-refresh" &&
            t.scope        == "activity"
        })
        1 * session.setAttribute("userId", _ as UUID)
        result.fitbitUserId == fitbitUserId
    }

    def "handleCallback should update existing tokens when user already exists"() {
        given:
        def fitbitUserId = "existing-user"
        def existingUserId = UUID.randomUUID()
        def existingUser = User.builder()
                .id(existingUserId)
                .fitbitUserId(fitbitUserId)
                .build()
        def existingToken = OAuthToken.builder()
                .id(UUID.randomUUID())
                .userId(existingUserId)
                .accessToken("old-enc-access")
                .refreshToken("old-enc-refresh")
                .expiresAt(LocalDateTime.now().plusHours(1))
                .scope("activity")
                .build()

        def tokenResponse = [
            access_token : "new-raw-access",
            refresh_token: "new-raw-refresh",
            expires_in   : 28800,
            user_id      : fitbitUserId,
            scope        : "activity",
        ] as Map<String, Object>

        fitbitOAuthClient.exchangeCodeForToken("auth-code") >> tokenResponse
        userMapper.findByFitbitUserId(fitbitUserId)         >> Optional.of(existingUser)
        tokenEncryptionService.encrypt("new-raw-access")    >> "new-enc-access"
        tokenEncryptionService.encrypt("new-raw-refresh")   >> "new-enc-refresh"
        oAuthTokenMapper.findByUserId(existingUserId)       >> Optional.of(existingToken)

        when:
        def result = service.handleCallback("auth-code", session)

        then:
        0 * userMapper.insert(_)
        1 * oAuthTokenMapper.update({ OAuthToken t ->
            t.accessToken  == "new-enc-access" &&
            t.refreshToken == "new-enc-refresh"
        })
        result == existingUser
    }

    def "handleCallback should set userId in session"() {
        given:
        def fitbitUserId = "session-test-user"
        def tokenResponse = [
            access_token : "a",
            refresh_token: "r",
            expires_in   : 3600,
            user_id      : fitbitUserId,
            scope        : "activity",
        ] as Map<String, Object>

        fitbitOAuthClient.exchangeCodeForToken(_)   >> tokenResponse
        userMapper.findByFitbitUserId(fitbitUserId)  >> Optional.empty()
        tokenEncryptionService.encrypt(_)            >> "enc"
        oAuthTokenMapper.findByUserId(_)             >> Optional.empty()

        when:
        service.handleCallback("code", session)

        then:
        1 * session.setAttribute("userId", _ as UUID)
    }

    // ─────────────────────────────────────────────────────────────────────
    // refreshToken
    // ─────────────────────────────────────────────────────────────────────

    def "refreshToken should decrypt the stored refresh token, call Fitbit, and persist new encrypted tokens"() {
        given:
        def userId = UUID.randomUUID()
        def existingToken = OAuthToken.builder()
                .id(UUID.randomUUID())
                .userId(userId)
                .accessToken("old-enc-access")
                .refreshToken("old-enc-refresh")
                .expiresAt(LocalDateTime.now().plusHours(1))
                .scope("activity")
                .build()

        def newTokenResponse = [
            access_token : "new-raw-access",
            refresh_token: "new-raw-refresh",
            expires_in   : 28800,
        ] as Map<String, Object>

        // All stubs defined in given: so they remain active during when:
        oAuthTokenMapper.findByUserId(userId)              >> Optional.of(existingToken)
        tokenEncryptionService.decrypt("old-enc-refresh")  >> "decrypted-refresh-token"
        fitbitOAuthClient.refreshToken("decrypted-refresh-token") >> newTokenResponse
        tokenEncryptionService.encrypt("new-raw-access")   >> "new-enc-access"
        tokenEncryptionService.encrypt("new-raw-refresh")  >> "new-enc-refresh"

        when:
        service.refreshToken(userId)

        then:
        // Verify the updated token was persisted with new encrypted values
        1 * oAuthTokenMapper.update({ OAuthToken t ->
            t.accessToken  == "new-enc-access" &&
            t.refreshToken == "new-enc-refresh"
        })
    }

    def "refreshToken should throw RuntimeException when token record is not found"() {
        given:
        def userId = UUID.randomUUID()
        oAuthTokenMapper.findByUserId(userId) >> Optional.empty()

        when:
        service.refreshToken(userId)

        then:
        def ex = thrown(RuntimeException)
        ex.message.contains(userId.toString())
    }
}
