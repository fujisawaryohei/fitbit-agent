# Tech Stack Decisions — Unit 2: Backend API

## 採用技術スタック

| カテゴリ | 技術 | バージョン | 採用理由 |
|---|---|---|---|
| Web フレームワーク | FastAPI | 0.115.x | 非同期対応・Pydantic統合・自動スキーマ生成 |
| ASGI サーバー | uvicorn | 0.34.x | FastAPI 標準 ASGI サーバー、`--reload` で開発効率 |
| HTTP クライアント（内部） | httpx | 0.28.x | Unit 1 から継続利用、非同期対応 |
| テスト | pytest-asyncio | 0.24.x | FastAPI 非同期エンドポイントのテスト |
| テスト HTTP クライアント | httpx.AsyncClient | — | FastAPI TestClient の非同期版 |

---

## 採用技術の詳細

### FastAPI

**採用理由**:
- Pydantic v2 によるリクエスト/レスポンスの自動バリデーション（BR-01, BR-06）
- `StreamingResponse` による SSE の簡潔な実装（BLM-01）
- `async def` による非同期エンドポイント（LangGraph の `astream()` と自然に統合）
- 自動生成される Swagger UI（`/docs`）で手動テストが容易

**設計上の注意**:
- `agent.stream()` ではなく `agent.astream()` を使用（非同期ジェネレータ）
- `StreamingResponse` のジェネレータは `async def` で定義する

---

### SSE（Server-Sent Events）実装方針

**FastAPI での SSE**:
```python
from fastapi.responses import StreamingResponse

return StreamingResponse(
    generator(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # nginx バッファリング防止
    }
)
```

**WebSocket を採用しない理由**:
- 単方向ストリーミング（サーバー → クライアント）のみ必要
- SSE はシンプルな HTTP/1.1 上で動作し、再接続も自動
- フロントエンド（Next.js）の `EventSource` API で直接受信可能

---

### OAuth2 フロー実装方針

**Authorization Code Flow（PKCEなし）**:
- Fitbit は Authorization Code Flow を標準サポート
- PoC スコープのためサーバーサイドでシークレットを管理（confidential client）
- PKCE は将来のモバイル/SPA 対応時に追加

**リダイレクトURI**:
```
開発: http://localhost:8000/auth/fitbit/callback
```

---

### pytest-asyncio 設定

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

**テストパターン**:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```
