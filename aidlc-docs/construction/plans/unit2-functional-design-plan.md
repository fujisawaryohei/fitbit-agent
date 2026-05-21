# Unit 2 Functional Design Plan — Backend API

## 実施ステップ

- [x] 1. ドメインエンティティ定義（domain-entities.md）
  - [x] 1-1. Request/Response モデル（ChatRequest, ChatResponse, AuthCallbackResponse, HealthResponse）
  - [x] 1-2. OAuth2 フロー中間エンティティ（OAuthState, TokenResponse）
  - [x] 1-3. SSE チャンク形式（SSEChunk）
  - [x] 1-4. エンティティ関係図

- [x] 2. ビジネスロジックモデル定義（business-logic-model.md）
  - [x] 2-1. チャットフロー（POST /chat → LangGraphAgent → SSE）
  - [x] 2-2. OAuth2 認可フロー（GET /auth/fitbit → Fitbit認可サーバー → callback）
  - [x] 2-3. ヘルスチェックフロー

- [x] 3. ビジネスルール定義（business-rules.md）
  - [x] 3-1. チャット入力バリデーション
  - [x] 3-2. OAuth2 state パラメータ検証
  - [x] 3-3. SSE イベント形式
