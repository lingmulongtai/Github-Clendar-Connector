# ✨ GitHub Calendar Connector

> Sync your GitHub contribution graph to Google Calendar, day by day.

A lightweight FastAPI service that reads GitHub contributions and upserts all-day events into Google Calendar.

---

## 🚀 Features

- **`POST /sync`** to fetch and sync daily contributions in a date range.
- **GitHub GraphQL API** integration via `contributionsCollection`.
- **Google Calendar upsert** using `extendedProperties.private.externalId`.
- **Automatic color mapping** by contribution count (`colorId`).
- **`dry_run` mode** to preview create/update counts without writing.
- **Explicit upstream error handling** (`502 Bad Gateway` for GitHub/Google failures).
- **Unit tests included** (settings, models, color mapping, sync logic, API clients).

---

## 🧱 Architecture at a glance

```text
Client
  -> FastAPI (/sync)
    -> SyncService
      -> GitHubClient (fetch contribution days)
      -> GoogleCalendarClient (upsert events)
```

---

## 🛠️ Quick Start

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Set environment variables

```bash
export GITHUB_TOKEN=ghp_xxx
export GOOGLE_ACCESS_TOKEN=ya29.xxx
```

### 3) Run the API

```bash
uvicorn app.main:app --reload
```

Open: `http://127.0.0.1:8000/docs`

---

## 📡 API Endpoints

### `GET /health`
Health check endpoint.

### `POST /sync`
Sync contribution days to Google Calendar.

#### Request example

```json
{
  "github_username": "octocat",
  "calendar_id": "primary",
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "show_zero_days": true,
  "dry_run": false
}
```

#### Response example

```json
{
  "synced_events": 31,
  "skipped_days": 5,
  "created_events": 20,
  "updated_events": 11,
  "dry_run": false
}
```

---

## ⚠️ Error Codes

- `400` Validation error (e.g., invalid date range)
- `500` Missing required environment variables
- `502` Upstream API error (GitHub / Google)

---

## 🧪 Testing

```bash
pytest -q
```

---

# 🇯🇵 日本語

GitHubのコントリビューション（草）を、日単位でGoogleカレンダーへ同期するFastAPIサービスです。

## 実装済み機能

- `POST /sync` で指定期間の日別コントリビューションを取得・同期
- GitHub GraphQL API（`contributionsCollection`）連携
- Google Calendar API 連携（`extendedProperties.private.externalId` でupsert）
- コントリビューション件数に応じた `colorId` を自動付与
- `dry_run` による書き込みなしの差分確認
- 上流API障害時に `502 Bad Gateway` を返す明示的エラーハンドリング
- ユニットテスト（設定検証・モデル検証・色マッピング・同期ロジック・APIクライアント）

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
export GITHUB_TOKEN=ghp_xxx
export GOOGLE_ACCESS_TOKEN=ya29.xxx
```

```bash
uvicorn app.main:app --reload
```

## API

### `GET /health`
ヘルスチェック。

### `POST /sync`
コントリビューション情報をGoogleカレンダーに同期します。

#### リクエスト例

```json
{
  "github_username": "octocat",
  "calendar_id": "primary",
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "show_zero_days": true,
  "dry_run": false
}
```

#### レスポンス例

```json
{
  "synced_events": 31,
  "skipped_days": 5,
  "created_events": 20,
  "updated_events": 11,
  "dry_run": false
}
```

## エラーコード

- `400`: バリデーションエラー（例: 日付範囲不正）
- `500`: 必須環境変数不足
- `502`: GitHub / Google の上流APIエラー

## テスト

```bash
pytest -q
```
