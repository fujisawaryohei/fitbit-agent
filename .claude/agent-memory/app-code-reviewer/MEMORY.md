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
- Allowed: @Getter, @RequiredArgsConstructor, @Builder, @Slf4j
- @NoArgsConstructor and @AllArgsConstructor are NOT in the allowed list per guidelines
- When @Builder is used with @NoArgsConstructor, @AllArgsConstructor is required for Lombok internals
- BUT: @NoArgsConstructor/@AllArgsConstructor themselves are not in the approved list
- Recommended pattern: use @Builder alone, or @RequiredArgsConstructor for DI

## Recurring Patterns / Common Mistakes Observed
- Session 1 (User.java review):
  - User used @NoArgsConstructor + @AllArgsConstructor with @Builder — @NoArgsConstructor/@AllArgsConstructor
    not in the approved Lombok list per guidelines
  - updateProfile() mutates @Getter-only fields — Lombok @Getter generates only getters,
    so direct field assignment works within the same class, but the design mixes
    immutable-style (all private) with mutable methods inconsistently
  - @Setter was NOT added (good), but updateProfile() directly assigns to private fields,
    which actually compiles fine in Java (same class), but is inconsistent with Lombok philosophy
  - updatedAt field not updated inside updateProfile() — a logical bug

## User Profile
- Java beginner — needs explanations of underlying principles, not just fix instructions
- Learning through pair programming style
- Appreciates educational context for why something is a problem
