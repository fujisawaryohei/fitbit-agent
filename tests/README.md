# テスト解説

## 構成

```
tests/
├── test_planning_tools.py      # calculate_calorie_deficit ユニットテスト
├── test_pbt_planning.py        # Hypothesis プロパティベーステスト
├── test_fitbit_client.py       # FitbitClient モックテスト
├── test_fitbit_tools.py        # fitbit_tools モックテスト
├── test_memory_manager.py      # MemoryManager モックテスト
├── test_models.py              # Pydantic モデル バリデーションテスト
└── test_planning_tools_llm.py  # LLM 呼び出しツール モックテスト
```

## 実行方法

```bash
# 全テスト実行
uv run python -m pytest tests/

# カバレッジ付き（未カバー行番号表示）
uv run python -m pytest tests/ --cov=. --cov-report=term-missing

# HTML レポート生成（htmlcov/index.html）
uv run python -m pytest tests/ --cov=. --cov-report=html
```

---

## 各テストファイルの解説

### test_planning_tools.py — ユニットテスト

`calculate_calorie_deficit` は外部依存がない純粋な計算ロジックなので、モックなしで検証できます。

```python
def invoke(current, target, pace=0.5):
    return calculate_calorie_deficit.invoke(
        {"current_weight_kg": current, "target_weight_kg": target, "pace_kg_per_week": pace}
    )

def test_daily_deficit_calculation():
    result = invoke(75.0, 70.0, pace=0.5)
    # 0.5kg/week * 7200kcal/kg / 7days = 514kcal
    assert "514kcal" in result
```

**テストケース**

| ケース | 内容 |
|---|---|
| 正常系 | 計算結果の文字列を検証 |
| 境界値 | pace=0.1（最小）、pace=1.0（最大）で clamp が効くか確認 |
| 異常系 | target >= current で ValueError、pace 範囲外で ValueError |

---

### test_pbt_planning.py — プロパティベーステスト（Hypothesis）

通常のテストは「特定の入力 → 特定の出力」を検証しますが、PBT は「**どんな入力でもこの性質が成り立つ**」を検証します。Hypothesis がランダムな値を大量生成して境界値を自動探索します。

```python
@given(
    current=st.floats(min_value=50, max_value=120),
    target=st.floats(min_value=40, max_value=119),
    pace=st.floats(min_value=0.1, max_value=1.0),
)
def test_daily_deficit_always_in_safe_range(current, target, pace):
    assume(target < current)  # 前提条件を満たすケースだけ実行
    result = invoke(current, target, pace)
    # 結果が常に安全範囲（200〜1000kcal）に収まるか
    daily_deficit = round(min(1000, max(200, round(pace * KCAL_PER_KG / 7))))
    assert str(daily_deficit) in result
```

`assume()` は前提条件を指定します。条件を満たさない入力は自動でスキップされます。

---

### test_fitbit_client.py — FitbitClient モックテスト

実際の Fitbit API を叩かずに検証します。`patch` で `httpx.get` を差し替えてレスポンスを制御します。

```python
def _mock_response(self, status_code, json_data=None, text=""):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    mock.text = text
    return mock

def test_get_activities_success(self, client, valid_token_env):
    expected = {"summary": {"steps": 8000}}
    with patch("httpx.get", return_value=self._mock_response(200, expected)):
        result = client.get_activities("2026-05-20")
    assert result == expected
```

`fixture` でテストの前処理を共通化しています。

```python
@pytest.fixture
def valid_token_env(monkeypatch):
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    monkeypatch.setenv("FITBIT_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("FITBIT_EXPIRES_AT", future)
```

`monkeypatch.setenv` はテスト終了後に自動で元に戻ります。

---

### test_fitbit_tools.py — fitbit_tools モックテスト

FitbitClient のメソッドをモックして、各ツールの文字列整形ロジックを検証します。

```python
MODULE = "tools.fitbit_tools._client"

def test_normal(self):
    with patch(f"{MODULE}.get_activities", return_value={"summary": {"steps": 8000}}):
        result = get_steps.invoke({"date": "2026-05-20"})
    assert result == "歩数: 8000歩"
```

`patch` のパスは「実際に使われている場所」を指定するのがポイントです。`fitbit.client.FitbitClient` ではなく `tools.fitbit_tools._client` を指定しています。

---

### test_memory_manager.py — MemoryManager モックテスト

DB 接続（psycopg2）と埋め込みモデルをモックして、SQL クエリの正しさとエラー時の挙動を検証します。

```python
def make_conn_mock(fetchall_return=None):
    cursor_mock = MagicMock()
    cursor_mock.__enter__ = lambda s: cursor_mock   # with 文対応
    cursor_mock.__exit__ = MagicMock(return_value=False)
    cursor_mock.fetchall.return_value = fetchall_return or []
    conn_mock = MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    return conn_mock
```

`with conn.cursor() as cur:` という `with` 文を MagicMock で再現するため、`__enter__` / `__exit__` を手動で設定しています。

**フォールバック確認**

```python
def test_returns_empty_on_db_error(self):
    conn_mock.cursor.return_value.execute.side_effect = Exception("DB error")
    result = search_memories("session-1", "クエリ")
    assert result == []  # エラー時は空リストを返す
```

---

### test_models.py — Pydantic モデル バリデーションテスト

Pydantic の `field_validator` が正しく機能するかを検証します。

```python
def test_invalid_pace_too_high(self):
    with pytest.raises(ValidationError):
        WeightGoal(current_weight_kg=75.0, target_weight_kg=70.0, pace_kg_per_week=1.5)
```

---

### test_planning_tools_llm.py — LLM 呼び出しツール モックテスト

`generate_home_workout_plan` / `get_weekly_progress` は関数内で `ChatAnthropic` を生成するため、クラスごと差し替えます。

```python
def make_llm_mock(content):
    response = MagicMock()
    response.content = content
    llm = MagicMock()
    llm.invoke.return_value = response
    return llm

def test_returns_llm_response(self):
    llm_mock = make_llm_mock("週3日の運動プラン...")
    with patch("tools.planning_tools.ChatAnthropic", return_value=llm_mock):
        result = generate_home_workout_plan.invoke({...})
    assert result == "週3日の運動プラン..."
```

`patch` の対象が `ChatAnthropic`（クラス）なので、`return_value` がインスタンスになります。

---

## カバレッジ結果

| ファイル | カバレッジ |
|---|---|
| tools/fitbit_tools.py | 100% |
| tools/planning_tools.py | 100% |
| memory/manager.py | 100% |
| fitbit/models.py | 100% |
| fitbit/client.py | 78% |
| **合計** | **83%** |

`agent/` 配下（LangGraph グラフ・ノード）は LLM とグラフ実行に依存するため単体テストの対象外としています。
