# テスト実行時に Bedrock クライアント初期化エラーで収集失敗

## 現象

`pytest` でテストを収集する際に以下のエラーが発生し、関係のないテストまで失敗する。

```
ERROR app/tests/controllers/test_health.py
pydantic_core._pydantic_core.ValidationError: 1 validation error for ChatBedrockConverse
  Value error, Could not load credentials to authenticate with AWS client.
```

## 原因

`test_health.py` が `from server import app` でアプリ全体をインポートする。

```
server.py → app/router.py → app/controllers/chat.py
  → _agent = get_agent()  ← モジュールレベルで実行
    → agent/nodes.py
      → _llm = ChatBedrockConverse(...)  ← インポート時に AWS 認証を試みる → 失敗
```

テスト環境には AWS 認証情報がないため、インポート時点でクラッシュする。

## 解決

`test_health.py`（および `test_auth.py`）を `server` 全体をインポートせず、
対象コントローラーの router だけをマウントした最小 FastAPI アプリでテストする。

```python
# before
from server import app

def test_health_returns_ok():
    client = TestClient(app)
    ...

# after
from fastapi import FastAPI
from app.controllers.health import router as health_router

_app = FastAPI()
_app.include_router(health_router)

def test_health_returns_ok():
    client = TestClient(_app)
    ...
```

`test_chat.py` では Bedrock 初期化を防ぐため、インポート前に `ChatBedrockConverse` をモックする。

```python
with patch("langchain_aws.ChatBedrockConverse", MagicMock()):
    from app.controllers.chat import router as chat_router
```

## 対象ファイル

- `app/tests/controllers/test_health.py`
- `app/tests/controllers/test_chat.py`
