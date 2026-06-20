# Project Overview: fitbit-agent

このプロジェクトの構成・技術スタック。計画・実装・レビューの各ステップで参照する。

## 技術スタック

| 領域 | 技術 |
|------|------|
| バックエンド | Python / FastAPI |
| エージェント | LangGraph（`agent/`） |
| フロントエンド | Next.js 16 / TypeScript / Tailwind CSS |
| DB マイグレーション | Alembic |
| パッケージ管理 | uv（`pyproject.toml` / `uv.lock`） |
| LLM | AWS Bedrock |

## ディレクトリ構成

| パス | 役割 |
|------|------|
| `backend/controllers/` | FastAPI エンドポイント |
| `backend/services/` | ビジネスロジック |
| `backend/repositories/` | データアクセス（Repository パターン） |
| `backend/decorators/` | 横断的関心事（ログマスク等） |
| `backend/tests/` | バックエンドのテスト |
| `backend/containers.py` | DI コンテナ |
| `agent/` | LangGraph のグラフ・ノード定義 |
| `frontend/src/` | Next.js アプリ |
| `qa-docs/` | 調査・QA ドキュメント |

## 設計上の約束

- イミュータブル設計（破壊的変更を避ける）
- Repository パターンでデータアクセスを抽象化
- 多数の小さなファイル（高凝集・低結合）
- 型注釈を整備し mypy を通す

## ツール実行

- Python の依存・実行は uv 経由（`uv run ...`）
- 共通コマンドは `Makefile` を参照する
