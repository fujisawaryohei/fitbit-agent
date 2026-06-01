# mypy 設定の解説

---

## Q. このプロジェクトの mypy 設定の意図は？

`pyproject.toml` の `[tool.mypy]` セクションは以下の方針で設定しています。

> 「**型注釈は必ず書く。ただしサードパーティライブラリの呼び出しは縛らない。**」

`strict = true`（すべてのチェックを有効化）は使わず、必要なルールだけを個別に有効化しています。

---

## Q. 各設定の意味は？

```toml
[tool.mypy]
python_version = "3.11"
disallow_untyped_defs = true
disallow_incomplete_defs = true
warn_return_any = true
warn_unused_ignores = true
```

| 設定 | 効果 |
|---|---|
| `python_version` | 型チェックの基準となる Python バージョン |
| `disallow_untyped_defs` | 型注釈のない関数定義をエラーにする |
| `disallow_incomplete_defs` | 一部だけ注釈した関数（引数はあるが戻り値がないなど）をエラーにする |
| `warn_return_any` | `Any` を返す関数に警告を出す |
| `warn_unused_ignores` | 不要になった `# type: ignore` コメントに警告を出す |

---

## Q. `strict = true` との違いは？

`strict = true` は以下の全項目を一括で有効にします。

| オプション | strict=true | このプロジェクト |
|---|---|---|
| `disallow_untyped_defs` | 有効 | **有効** |
| `disallow_incomplete_defs` | 有効 | **有効** |
| `warn_return_any` | 有効 | **有効** |
| `warn_unused_ignores` | 有効 | **有効** |
| `disallow_untyped_calls` | 有効 | **無効** ← ここが違う |
| `disallow_any_generics` | 有効 | **無効** |
| `disallow_any_expr` | 有効 | **無効** |

最大の違いは `disallow_untyped_calls`（型注釈のない関数の呼び出し禁止）を無効にしている点です。

`strict = true` でこれを有効にすると、LangGraph・LangChain・dependency-injector など型スタブが完全でないライブラリを呼び出すたびにエラーになります。これらは `# type: ignore` で抑制するか `ignore_missing_imports` で対処できますが、ノイズが多くなります。

---

## Q. テストファイルは設定が緩いのはなぜ？

テストは型注釈なしで書かれることが多く、`disallow_untyped_defs = true` を適用すると全テスト関数にアノテーションが必要になります。テストの可読性を優先するため、override で緩和しています。

```toml
[[tool.mypy.overrides]]
module = ["backend.tests.*", "agent.tests.*", "tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
warn_return_any = false
warn_unused_ignores = false
```

---

## Q. サードパーティライブラリの設定は？

型スタブが存在しないライブラリは `ignore_missing_imports = true` で import エラーを抑制しています。

```toml
[[tool.mypy.overrides]]
module = [
    "langgraph.*",
    "langchain.*",
    "langchain_core.*",
    "langchain_aws.*",
    "dependency_injector.*",
    "alembic.*",
    "pgvector.*",
]
ignore_missing_imports = true
```

これらのライブラリはスタブが存在しない・または不完全なため、import 自体をエラーにしないようにしています。実際の呼び出し結果は `Any` として扱われます。

---

## Q. `types-psycopg2` はなぜ必要？

`psycopg2` は型スタブが本体に含まれておらず、別パッケージ `types-psycopg2` として提供されています。

リポジトリクラスの `__init__` で `conn: psycopg2.extensions.connection` のような型注釈を使うために必要です。

```python
import psycopg2.extensions

class ChatRepository:
    def __init__(self, conn: psycopg2.extensions.connection) -> None:
        self.conn = conn
```

`types-psycopg2` がないと mypy が `psycopg2.extensions` を認識できず `import-untyped` エラーになります。

---

## Q. mypy の実行方法は？

```bash
uv run mypy .
```

成功時の出力：

```
Success: no issues found in 63 source files
```
