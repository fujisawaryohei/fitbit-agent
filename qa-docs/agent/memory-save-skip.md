# 長期記憶に "SKIP" が大量保存される

## 現象

`memories` テーブルに以下のようなレコードが大量に保存される。

```
[{'type': 'text', 'text': 'SKIP', 'index': 0}]
[{'type': 'text', 'text': 'SKIP', 'index': 0}]
...
```

## 原因

Bedrock（`ChatBedrockConverse`）の応答は `AIMessage.content` が文字列ではなくリスト形式で返る。

```python
# Bedrock の応答形式
summary.content = [{'type': 'text', 'text': 'SKIP', 'index': 0}]

# str() に渡すと以下になり "SKIP" と一致しない
str(summary.content) == "[{'type': 'text', 'text': 'SKIP', 'index': 0}]"
```

`if str(summary.content).strip() != "SKIP"` の条件が常に True になり、SKIP 判定が機能しなかった。

## 解決

`_extract_text()` ヘルパーを追加してリスト形式からテキストを抽出した後に比較する。

```python
def _extract_text(content: object) -> str:
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)

# memory_save_node 内
content = _extract_text(summary.content)
if content.strip() != "SKIP":
    save_memory(state.session_id, content)
```

同じ問題が会話履歴の構築にもあったため `_extract_text()` で統一。

## 対象ファイル

- `agent/nodes.py`
