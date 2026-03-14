# App Code Reviewer - Persistent Memory

## Project Overview
- Backend: Java 21 + Spring Boot 3.x + MyBatis 3.0.3 + PostgreSQL
- Frontend: React 18 + TypeScript + Vite
- ORM: MyBatis (NOT JPA/Hibernate)
- Lombok: @Getter, @RequiredArgsConstructor, @Builder, @Slf4j のみ許可 (guidelines 2.1)
- MyBatis config: map-underscore-to-camel-case: true (snake_case DB -> camelCase Java)

## Key Architectural Rules
- Layer order: Controller -> Service -> Repository (Persistence Layer uses MyBatis Mapper)
- Domain entities are POJOs in com.fitbitagent.domain.entity — NO JPA annotations
- Field injection (@Autowired) is FORBIDDEN — use constructor injection
- Optional: use only as return value, NOT for fields or parameters

## Lombok Rules (Important)
- Allowed globally: @Getter, @RequiredArgsConstructor, @Builder, @Slf4j
- Exception for domain/entity classes only: @NoArgsConstructor and @AllArgsConstructor are ALSO allowed
  (per guidelines 2.1 — updated after Session 1 review feedback)
- Recommendation: When using @AllArgsConstructor with @Builder in entities, consider restricting
  access level (e.g., AccessLevel.PACKAGE) since external callers should use the builder
- Recommended pattern for DI classes: @RequiredArgsConstructor only

## Recurring Patterns / Common Mistakes Observed
- Session 1 (User.java review):
  - User used @NoArgsConstructor + @AllArgsConstructor with @Builder (now clarified as allowed for entities)
  - updateProfile() mutates @Getter-only fields — direct field assignment works within same class in Java
  - updatedAt field not updated inside updateProfile() — a logical bug

- Session 2 (OAuthToken.java initial review):
  - SAME naming mistake as User.java: snake_case field names (user_id, expires_at) instead of camelCase
    (userId, expiresAt). MyBatis map-underscore-to-camel-case=true handles the DB<->Java conversion
    automatically — Java fields must always be camelCase regardless of DB column names.
  - Required business logic methods (updateTokens(), isExpired()) were completely missing
    despite being listed in the task requirements. Check that all specified methods are implemented.
  - Naming convention violation is a recurring mistake — likely to appear in future entity classes too.

- Session 3 (OAuthToken.java re-review after Must fixes):
  - camelCase field names were correctly fixed (good progress).
  - isExpired() logic was correct but missing `return` keyword — compiled to a no-op expression statement.
    This is a classic beginner mistake: forgetting `return` in non-void methods.
  - Method name typo: `updateToken` (singular) instead of required `updateTokens` (plural).
    Watch for spec-vs-implementation name mismatches in future reviews.

- Session 4 (OAuthToken.java — all Must fixes confirmed resolved):
  - Both Session 3 Must items were correctly fixed: `return` added, method renamed to `updateTokens`.
  - Remaining Should: isExpired() does not guard against null `expiresAt` — @NoArgsConstructor means
    null is reachable. Raised as Should (not Must) since it's defensive programming, not a current bug.
  - Nit: Lombok imports not in alphabetical order within the same package group.
  - OAuthToken.java is now considered implementation-complete and can move to the next task.

- Session 5 (TokenEncryptionService.java — initial review):
  - Critical: IV zero-filled instead of SecureRandom-generated — breaks AES-GCM security.
  - Critical: encrypt() used GCM_IV_LENGTH (12) as tag length arg instead of GCM_TAG_LENGTH (128).
  - Class missing @Service annotation; no @Slf4j.
  - Property key typo: "app.token-enctyption-key" (missing 'r').
  - Variable name `KeyBytes` (UpperCamelCase) instead of `keyBytes`.
  - plainText.getBytes() and new String(bytes) without StandardCharsets.UTF_8.

- Session 6 (TokenEncryptionService.java — re-review after Must fixes):
  - All Session 5 critical/security Must items CORRECTLY FIXED: SecureRandom IV, GCM_TAG_LENGTH
    consistency, @Service added, @Slf4j added.
  - STILL UNRESOLVED (carried over as Must this session):
    1. Property key typo: "enctyption" still present at line 24 — startup failure risk.
    2. plainText.getBytes() still missing StandardCharsets.UTF_8 (line 37).
    3. new String(cipher.doFinal(encrypted)) still missing StandardCharsets.UTF_8 (line 59).
  - STILL UNRESOLVED (Should): `KeyBytes` naming at line 25, broad exception handling with no logging.
  - Pattern: User fixes security-critical Must items quickly but misses Should/Nit items from
    previous sessions. Consider explicitly tracking carryover items between sessions.

- Session 7 (FitbitOAuthClient.java — initial review):
  - Two typos in refreshToken() request parameters: "grand_type" (grant), "refresh_toekn" (token).
    These are silent runtime bugs — no compile error, but Fitbit API returns 400/error at runtime.
    Reinforces the pattern of string literal typos being hard to catch without tests.
  - FitbitApiException placed in com.fitbitagent.client.fitbit.exception instead of
    com.fitbitagent.exception as defined in docs/architecture.md 3.2. This is a package placement
    violation — exception classes must all live under com.fitbitagent.exception for GlobalExceptionHandler
    to work correctly.
  - callTokenEndpoint() was public but should be private (internal helper method).
  - Map.class used as raw type with @SuppressWarnings("unchecked") — recommended to use typed DTO instead.

- Session 8 (OAuthService.java — initial review):
  - CRITICAL BUG: refreshToken() calls token.updateTokens() but omits oAuthTokenMapper.update(token).
    MyBatis does NOT auto-track entity changes (unlike JPA Dirty Checking). Mapper update() must be
    called explicitly. This pattern must be verified in all future Service methods that modify entities.
  - RuntimeException used directly in refreshToken() instead of ResourceNotFoundException.
    Architecture doc 3.2 defines ResourceNotFoundException in com.fitbitagent.exception — always use
    domain-specific exceptions so GlobalExceptionHandler can map them to correct HTTP codes.
  - tokenResponse fields extracted without null checks — NullPointerException risk when Fitbit API
    returns unexpected response (missing fields). Service layer must validate external API responses.
  - HttpSession injected into Service layer (handleCallback signature) — HTTP concerns should stay
    in Controller layer per architecture doc 3.3. Raised as Should since atomicity intent is valid.
  - @Slf4j missing — architecture doc 8.2 requires INFO logging for major business events like login.
  - No test file exists yet (src/test/groovy/com/fitbitagent/service/) — guidelines require tests
    before task is considered Done.

- Session 9 (AuthController.java — initial review):
  - CRITICAL import bug: `org.springframework.web.reactive.result.view.RedirectView` (WebFlux) used
    instead of `org.springframework.web.servlet.view.RedirectView` (Spring MVC). Both are on classpath
    since pom.xml includes spring-boot-starter-webflux for WebClient. Compiles but redirect won't work
    at runtime. Always verify Spring MVC vs WebFlux stack when using view-related classes.
  - Security guard: savedState null check missing. When session expires before callback, `savedState`
    is null. `state.equals(null)` returns false safely, but the log message `Expected: null` is
    misleading. Explicit null guard on savedState improves clarity.
  - Naming mismatch: architecture.md 3.2 defines the class as `AuthService` but implementation uses
    `OAuthService`. Variable name `authService` in the controller partially masks this inconsistency.
  - No test file for Controller layer yet — guidelines 4.4 requires tests before task is Done.
  - Good: CSRF state pattern correctly implemented. @Slf4j, @RequiredArgsConstructor correct. Layer
    responsibility properly maintained (Controller delegates to Service, no business logic in Controller).

- Session 10 (GlobalExceptionHandler.java — initial review):
  - SECURITY Must: FitbitApiException.getMessage() returned directly to client — may expose Fitbit API
    internal error details. Always return safe fixed messages to clients; log the full exception server-side.
  - Design Must: Response format uses Map<String, String> (flat) but architecture.md 8.1 defines a
    nested JSON schema: { "error": { "code": "...", "message": "...", "details": {...} } }.
    ErrorResponse.java DTO (defined in architecture.md 3.2 package structure) was never created.
  - Completeness Must: Only FitbitApiException and RuntimeException handlers exist. Missing handlers for:
    ClaudeApiException, RateLimitExceededException, ResourceNotFoundException, MethodArgumentNotValidException.
    The corresponding exception classes also do not exist yet in the exception package.
  - Without ResourceNotFoundException handler, 404 cases fall through to RuntimeException and return 500.
  - Without MethodArgumentNotValidException handler, 400 validation errors return 500.
  - Should: FitbitApiException maps to a single 502, but architecture.md 8.1 defines two codes:
    FITBIT_API_ERROR (502) and FITBIT_RATE_LIMITED (429) — needs to differentiate by error type.
  - Should: No fallback Exception handler — uncaught checked exceptions bypass the unified error format.
  - Pattern: User tends to implement the minimum viable handler without considering the full exception
    taxonomy defined in architecture.md 8.1. Always cross-check the error code table when reviewing
    GlobalExceptionHandler changes.

## User Profile
- Java beginner — needs explanations of underlying principles, not just fix instructions
- Learning through pair programming style
- Appreciates educational context for why something is a problem
