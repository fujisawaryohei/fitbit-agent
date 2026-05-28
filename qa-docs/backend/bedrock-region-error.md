# Bedrock 起動時に「You must specify a region」エラー

## 現象

`uv run uvicorn server:app` 起動時に以下のエラーが発生しサーバーが起動しない。

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for ChatBedrockConverse
  Value error, Could not load credentials to authenticate with AWS client.
  Service error: You must specify a region.
```

## 原因

`agent/nodes.py` と `agent/tools/planning_tools.py` の `ChatBedrockConverse` 初期化時に `region_name` を指定していなかった。
EC2 インスタンスプロファイル認証であっても、Bedrock クライアントはリージョンを明示的に指定する必要がある。

## 解決

`ChatBedrockConverse` に `region_name="ap-northeast-1"` を追加。

```python
# before
_llm = ChatBedrockConverse(model="jp.anthropic.claude-haiku-4-5-20251001-v1:0").bind_tools(_tools)

# after
_llm = ChatBedrockConverse(model="jp.anthropic.claude-haiku-4-5-20251001-v1:0", region_name="ap-northeast-1").bind_tools(_tools)
```

## 対象ファイル

- `agent/nodes.py`
- `agent/tools/planning_tools.py`
