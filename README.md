# GitHub Calendar Connector

GitHubのコントリビューション（草）をGoogleカレンダーに同期するAPIです。

## 実装済み機能

- `POST /sync` で指定期間の日別コントリビューションを取得
- GitHub GraphQL API (`contributionsCollection`) 連携
- Google Calendar API 連携（`externalId` でupsert）
- コントリビューション件数に応じた `colorId` 付与
- `dry_run` で書き込みなしの差分確認
- 上流API障害時に `502 Bad Gateway` を返す明示的エラーハンドリング
- ユニットテスト（設定検証・モデル検証・色マッピング・同期ロジック）

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
リクエスト:

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

レスポンス:

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
- `502`: GitHub/Google 上流APIエラー

## テスト

```bash
pytest -q
```
