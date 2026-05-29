# DI コンテナ・Depends・ワイヤリングの解説

---

## Q. `Depends` とは何か？（dependency-injector なしの一般的な使い方）

FastAPI の組み込み DI（依存性注入）機能です。「**この引数は自分で用意するのではなく、FastAPI に用意してもらう**」という宣言です。

本来の使い方は、**関数を `Depends` に渡す**だけです。dependency-injector は不要です。

```python
# 依存関係を返す関数を定義する
def get_user_repo() -> UserRepository:
    conn = get_connection()
    return UserRepository(conn)

# Depends に渡す → FastAPI がリクエスト時に呼んでインスタンスを渡してくれる
@router.post("/chat")
def chat(
    user_repo: UserRepository = Depends(get_user_repo),
):
    user = user_repo.find_by_fitbit_user_id(...)
```

### `yield` を使ったクリーンアップ

`Depends` に渡す関数が `yield` を使うと、**リクエスト完了後のクリーンアップ**が書けます。

```python
def get_conn():
    conn = get_connection()
    try:
        yield conn           # ← ここでエンドポイントに制御を渡す
    finally:
        release_connection(conn)  # ← レスポンス送信後にここが実行される

@router.post("/chat")
def chat(
    conn = Depends(get_conn),
):
    # conn を使った処理
```

### テスト時の差し替え

FastAPI は `app.dependency_overrides` で差し替えができます。

```python
# テスト
app.dependency_overrides[get_user_repo] = lambda: mock_user_repo

client = TestClient(app)
response = client.post("/chat", ...)

app.dependency_overrides.clear()
```

---

## Q. このプロジェクトで `Depends(Provide[Container.user_repo])` を使っている理由

このプロジェクトでは FastAPI の素の `Depends` ではなく、**`dependency-injector`** ライブラリを組み合わせています。

```python
Depends(get_user_repo)                    # FastAPI 素の Depends
Depends(Provide[Container.user_repo])     # dependency-injector との組み合わせ
```

`Provide[Container.user_repo]` は dependency-injector が提供する「**コンテナのプロバイダを FastAPI の Depends に繋ぐアダプタ**」です。

### なぜ素の Depends を使わないのか

素の `Depends(get_user_repo)` では、テストの差し替えは `app.dependency_overrides` を使います。しかしこの方法は **FastAPI アプリのインスタンスに直接触る**必要があり、テスト間の状態管理が複雑になります。

`dependency-injector` を使うと、コンテナ側で一元管理でき、`container.user_repo.override(mock)` というシンプルな差し替えができます。

```python
# 素の Depends のテスト
app.dependency_overrides[get_user_repo] = lambda: mock_user_repo
# テスト後に忘れず消す必要がある
app.dependency_overrides.clear()

# dependency-injector のテスト
with container.user_repo.override(mock_user_repo):
    ...
# with を抜けると自動で元に戻る（消し忘れなし）
```

---

## Q. `Provide[Container.xxx]` と `@inject` の仕組み

```python
@router.post("/chat")
@inject  # ← これが必要
def chat(
    user_repo: UserRepository = Depends(Provide[Container.user_repo]),
):
```

`@inject` は dependency-injector が関数をラップして「`Provide[...]` を見つけたら対応するプロバイダからインスタンスを取得せよ」と指示するデコレータです。これがないと `Provide[...]` は解決されません。

---

## Q. ワイヤリングとは何か？

「**コンテナとコードを繋ぐ配線作業**」です。

`@inject` デコレータが `Provide[Container.user_repo]` を「目印」として持っていても、**どのコンテナインスタンスを使うか**はワイヤリングで決まります。

```python
container = Container()
container.wire(modules=["backend.controllers.chat"])
# ↑ 「chat モジュールの @inject 付き関数はこの container を使え」と配線する
```

内部的には、ワイヤリングによって関数のデフォルト引数が書き換えられ、
リクエスト時に `container.user_repo()` が呼ばれるようになります。

### プロジェクトでの設定

```
server.py（本番）
  container = Container()
  container.wire(modules=["backend.controllers.auth", "backend.controllers.chat"])

backend/tests/conftest.py（テスト）
  c = Container()
  c.wire(modules=["backend.controllers.auth", "backend.controllers.chat"])
  yield c
  c.unwire()
```

---

## Q. なぜ `conftest.py` の fixture は `yield` を使うのか？

### `yield` を使わない場合（return）

```python
@pytest.fixture(scope="session")
def container():
    c = Container()
    c.wire(modules=["backend.controllers.auth", "backend.controllers.chat"])
    return c  # ← ここで終わり。unwire が呼ばれない
```

テストが全部終わっても `c.unwire()` が呼ばれません。
ワイヤリング（モジュールへの書き換え）が残り続け、他のテストスイートに影響が出る可能性があります。

### `yield` を使う場合（推奨）

```python
@pytest.fixture(scope="session")
def container():
    c = Container()
    c.wire(modules=["backend.controllers.auth", "backend.controllers.chat"])
    yield c       # ← ここでテストに制御を渡す
    c.unwire()    # ← 全テスト終了後にここが実行される（クリーンアップ）
```

`yield` を使うことで fixture が「**セットアップ → テスト実行 → クリーンアップ**」の3段階になります。

### 仕組みレベルの説明

Python のジェネレーター関数は `yield` で処理を一時停止できます。pytest はこれを利用して以下のように動作します：

```
1. fixture 関数を呼び出す → ジェネレーターオブジェクトが作られる
2. next() でジェネレーターを進め、yield まで実行（セットアップ）
3. yield した値（コンテナ）をテスト関数の引数に渡す
4. テスト関数を実行
5. テスト終了後、再度 next() でジェネレーターを進める（yield 以降 = クリーンアップ）
```

pytest が内部でやっていること：

```python
gen = container_fixture()   # ジェネレーター生成
c = next(gen)               # yield まで実行してコンテナを取得 → テストに渡す
# ... テスト実行 ...
try:
    next(gen)               # yield 以降を実行（unwire が走る）
except StopIteration:
    pass                    # ジェネレーター終了
```

`scope="session"` により、テストセッション全体で1回だけセットアップ・クリーンアップが行われます。

---

## Q. テストでどうモックに差し替えるか？

`container.xxx.override(mock)` をコンテキストマネージャで使います。

```python
def test_unknown_user_returns_401(self, container):
    mock_user_repo = MagicMock()
    mock_user_repo.find_by_fitbit_user_id.return_value = None

    with container.user_repo.override(mock_user_repo):
        client = TestClient(_app)
        response = client.post("/chat", json={"message": "こんにちは"})

    assert response.status_code == 401
    # with を抜けると自動で元のプロバイダに戻る
```

### なぜコンテナはテスト全体で1つにする必要があるか？

ワイヤリングは「**どのコンテナインスタンスが差し替えを管理するか**」を紐付けます。

```
# NG: 2つのテストファイルがそれぞれ Container() を作ると
test_auth.py → Container(A) → auth, chat をワイヤリング
test_chat.py → Container(B) → auth, chat をワイヤリング（A を上書き！）

# test_auth.py が A.override(mock) しても、実際に使われるのは B → mock が効かない
```

`conftest.py` で1つのコンテナを作り `scope="session"` で共有することで解決しています。

---

## Q. FitbitService を `providers.Singleton` にした理由

`providers.Factory`（dependency-injector のデフォルト的な挙動）は**呼び出しのたびに新しいインスタンスを作ります**。

`FitbitService` は内部に `state_store`（CSRF トークンの一時保存場所）を持っています。

```python
class FitbitService:
    def __init__(self, ...):
        self._state_store: dict[str, CsrfState] = {}

    def get_authorization_url(self):
        state = CsrfState.generate()
        self._state_store[state.value] = state  # リクエスト1: state を保存

    def exchange_code_for_token(self, code, state):
        if state not in self._state_store:      # リクエスト2: state を検証
            raise InvalidStateError()           # ← 別インスタンスなら空で必ず失敗！
```

`providers.Factory` だと認証フローが壊れるため、`providers.Singleton`（1インスタンスを使い回し）にしています。

---

## Q. `_sse_generator` の DB コネクションだけ Depends に乗せなかった理由

`Depends(get_conn)` の `yield` クリーンアップは「**エンドポイント関数が return するタイミング**」で実行されます。

しかし `StreamingResponse` はエンドポイントが return した**後もストリーミングし続けます**。

```
エンドポイント return
  → Depends のクリーンアップ（conn が解放される）← ここで接続が切れる！
  → まだストリーミング中... → DB アクセスしようとして失敗
```

そのため `_sse_generator` に渡す conn だけは `get_connection()` で手動取得し、`finally` でストリーミング完了後に解放しています。

```python
# controllers/chat.py
conn = get_connection()       # 手動取得（Depends を使わない）
return StreamingResponse(
    _sse_generator(..., conn=conn, ...),
    ...
)

async def _sse_generator(..., conn, ...):
    try:
        ...                   # ストリーミング処理
    finally:
        release_connection(conn)  # ストリーミング完了後に解放
```
