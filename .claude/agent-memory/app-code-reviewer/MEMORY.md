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

## User Profile
- Java beginner — needs explanations of underlying principles, not just fix instructions
- Learning through pair programming style
- Appreciates educational context for why something is a problem
