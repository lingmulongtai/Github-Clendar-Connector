# GitHub Calendar Connector

GitHubのコントリビューション（草）を、Googleカレンダー等に同期するためのスタータープロジェクトです。

## 現在の実装（MVP）

- FastAPIベースのAPIサーバー
- コントリビューション件数を5段階にレベル化
- レベルに応じてGoogle Calendar `colorId` を割り当て
- 同期処理の土台（スタブ実装）

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

### `GET /health`
ヘルスチェック。

### `POST /sync`
指定ユーザーの指定期間のコントリビューションを同期する（現状はスタブ）。

リクエスト例:

```json
{
  "github_username": "octocat",
  "calendar_id": "primary",
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "show_zero_days": true
}
```

## 次の実装候補

1. GitHub OAuth + GraphQL `contributionsCollection` 本実装
2. Google OAuth + Calendar Events insert/upsert 本実装
3. externalId (`github:{username}:{date}`) で重複防止
4. 定期実行（Cloud Scheduler / cron）
