# Morning News Digest

毎朝、当日の主要ニュースを Claude Code（WebSearch）で自動収集・日本語要約し、
Google カレンダーに **7:00–7:30 JST の予定** として登録する GitHub Actions 連携リポジトリです。

PC を起動しておく必要はなく、すべて GitHub のクラウド上で動作します。

---

## 1. 概要と仕組み

```
┌──────────────────────┐   cron (21:00 UTC = 翌 06:00 JST)
│ GitHub Actions       │ ─────────────────────────────────┐
│ daily-news.yml       │                                  │
└──────────┬───────────┘                                  │
           │ 1) Claude Code (headless)                    │
           │    prompts/news-digest.md を実行             │
           │    WebSearch で当日ニュース収集・要約        │
           │    digest.json を書き出し                    │
           ▼                                              │
     ┌───────────┐                                        │
     │ digest.json│ { "description_html": "<HTML>" }      │
     └─────┬─────┘                                        │
           │ 2) Python                                    │
           │    scripts/create_calendar_event.py          │
           │    refresh_token → access_token              │
           │    今日 7:00–7:30 JST の予定を作成           │
           ▼                                              │
   ┌────────────────────┐                                 │
   │ Google Calendar    │ ☕ 今朝のニュースまとめ（M/D）  │
   └────────────────────┘                                 │
```

- **トリガー**: `cron: "0 21 * * *"`（UTC = 翌 06:00 JST）と `workflow_dispatch`（手動実行）
- **ニュース収集**: `claude -p ... --allowedTools "WebSearch,WebFetch,Write"`
- **カレンダー登録**: Google Calendar API v3 `events.insert`（タイムゾーン `Asia/Tokyo`）

---

## 2. Google Cloud のセットアップ

1. **プロジェクト作成**: [Google Cloud Console](https://console.cloud.google.com/) で新規プロジェクトを作成（既存でも可）。
2. **API 有効化**: 「API とサービス → ライブラリ」で **Google Calendar API** を有効化。
3. **OAuth 同意画面の構成**:
   - User Type: **External**（個人 Google アカウントの場合）
   - スコープに `https://www.googleapis.com/auth/calendar.events` を追加
   - テストユーザーに自分の Google アカウントを追加（公開ステータスが「テスト」のままで OK）
4. **OAuth クライアント ID を作成**:
   - 「認証情報 → 認証情報を作成 → OAuth クライアント ID」
   - アプリケーションの種類: **デスクトップ アプリ**
   - 作成後、JSON をダウンロードしてリポジトリ直下に **`client_secret.json`** という名前で保存
   - （`.gitignore` 済みなので誤コミットの心配はありません）

---

## 3. リフレッシュトークンの取得（ローカルで一度だけ）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/get_refresh_token.py
```

ブラウザが開いて Google 認証画面が表示されます。テストユーザーとして
登録した自分のアカウントで承認すると、ターミナルに次の 3 つの値が表示
されます。控えておいてください。

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

> リフレッシュトークンが空で返ってきた場合は、
> [Google アカウントのアクセス権限](https://myaccount.google.com/permissions)
> から該当クライアントのアクセスを解除してから再実行してください。

---

## 4. GitHub の Secrets 登録

リポジトリの **Settings → Secrets and variables → Actions → New repository secret** から
以下を登録します。

| Secret 名 | 内容 |
| --- | --- |
| `ANTHROPIC_API_KEY` | Anthropic Console で発行した API キー（**従量課金**） |
| `GOOGLE_CLIENT_ID` | 手順 3 で取得 |
| `GOOGLE_CLIENT_SECRET` | 手順 3 で取得 |
| `GOOGLE_REFRESH_TOKEN` | 手順 3 で取得 |
| `GOOGLE_CALENDAR_ID` | （任意）特定カレンダーに登録したい場合のみ。未設定なら `primary`（メインカレンダー）に登録 |

---

## 5. push 手順

```bash
git add .
git commit -m "Initial commit: morning news digest workflow"
git push -u origin main
```

> `client_secret.json` と `digest.json` は `.gitignore` で除外済みです。

---

## 6. 手動実行で動作確認

1. GitHub の **Actions** タブを開く
2. 左サイドバーから **Daily News Digest** ワークフローを選択
3. 右側の **Run workflow** ボタン → ブランチを選んで実行
4. 緑のチェックが付いたら、Google カレンダーの今日 7:00–7:30 に
   「☕ 今朝のニュースまとめ（M/D）」が登録されていることを確認

ジョブのログ末尾には作成された予定の `htmlLink` が出力されます。

---

## 7. cron 時刻の調整

`.github/workflows/daily-news.yml` の `cron` を編集します。

- GitHub Actions の **cron は UTC** で指定します。
- 既定値 `"0 21 * * *"` は **21:00 UTC = 翌 06:00 JST** 起動です。
- 7:00 JST までに完了させるため、**1 時間ほど余裕**を持たせています。
- 例: 5:30 JST に起動したい場合 → JST 5:30 = UTC 20:30 → `"30 20 * * *"`

---

## 注意点

- **GitHub Actions の定期実行は数分〜十数分の遅延**があります。確実に
  7:00 JST までに登録したい場合は、cron をさらに前倒しにしてください。
- **`WebSearch` ツールは米国（US）リージョンからのみ利用可能**です。
  GitHub Actions の `ubuntu-latest` ランナーは通常 US 圏で稼働するため
  問題なく動作します。セルフホストランナーを使う場合はリージョンに注意
  してください。
- **`ANTHROPIC_API_KEY` は従量課金**です。Claude.ai のサブスクリプションとは
  別物で、API 呼び出しごとに課金されます。Anthropic Console の Usage で
  使用量を確認してください。
- リフレッシュトークンは OAuth 同意画面の公開ステータスが「テスト」の
  場合 **7 日で失効**することがあります。長期運用する場合は同意画面を
  「本番環境」に切り替えてください（個人利用範囲なら審査不要）。
