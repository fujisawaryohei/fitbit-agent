package com.fitbitagent.controller;

import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.view.RedirectView;

import com.fitbitagent.service.OAuthService;

import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
@Slf4j
public class AuthController {
    
    private final OAuthService authService;

    @GetMapping("/login")
    public RedirectView login(HttpSession session) {
        String state = UUID.randomUUID().toString();
        session.setAttribute("oauth_state", state);
        String authorizationUrl = authService.buildAuthorizationUrl(state);
        return new RedirectView(authorizationUrl);
    }

    @GetMapping("/callback")
    public RedirectView callback(@RequestParam String code,
                                  @RequestParam String state,
                                  HttpSession session) {
        String savedState = (String) session.getAttribute("oauth_state");
        if (savedState == null || !savedState.equals(state)) {
            log.warn("OAuth state mismatch. Expected: {}, Got: {}", savedState, state);
            return new RedirectView("/login?error=invalid_state");
        }

        authService.handleCallback(code, session);
        return new RedirectView("/dashboard");
    }

    @PostMapping("/logout")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void logout(HttpSession session) {
        session.invalidate();
    }
}
