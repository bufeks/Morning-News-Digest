# Morning News Digest

毎朝、当日の主要ニュースを Claude Code（WebSearch）で自動収集・日本語要約し、
Google カレンダーに **7:00–7:30 JST の予定** として登録するための **Claude Code スラッシュコマンド** リポジトリです。

ダイジェストは **株式会社kiCk** のメンバー向けにチューニングされており、
一般的な経済・国内外・テクノロジーに加えて、

- **kiCk クライアント／関連業界の動向**（adidas、PILOT、Schick、Calbee、TOTO、旭化成ホームズ ほか）
- **経営レイヤーと話すときに役立つインサイト**（経営者発言・M&A・ガバナンス・戦略動向など）

の 2 セクションを含みます。

---

## 仕組み

```
あなたが Claude Code で /morning-digest と入力
        │
        ▼
.claude/commands/morning-digest.md の指示が読み込まれる
        │
        ├─ WebSearch / WebFetch で当日の主要ニュース 5 分野を収集・要約
        │
        ├─ HTML 形式で本文を組み立て
        │
        └─ Google Calendar MCP の create_event を呼んで
           今日 7:00–7:30 JST の予定を作成
```

GitHub Actions や Python スクリプト、OAuth 設定は **一切不要**。
Claude Code に既に接続済みの Google Calendar MCP の認証をそのまま使います。

クライアント／業界リストの編集は `.claude/commands/morning-digest.md` を直接編集してください。

---

## 使い方

### A. 手動で毎朝走らせる

1. このリポジトリを Claude Code（CLI / デスクトップ / web のいずれか）で開く
2. Google Calendar MCP が接続されていることを確認（接続されていなければ初回だけ MCP を追加）
3. プロンプト欄で `/morning-digest` と入力 → Enter
4. 数十秒〜数分で Web 検索 → 本文組み立て → カレンダー登録まで自動実行
5. 完了報告メッセージに作成した予定のリンクが表示される

### B. Claude Code on the web で **スケジュール実行** する（PC 起動不要）

Claude Code on the web の **Scheduled Trigger** を使うと、PC を起動していなくても毎朝自動で `/morning-digest` を走らせられます。

1. https://claude.ai/code でこのリポジトリを source として登録
2. **Triggers** → **Add scheduled trigger**
3. Cron 設定: **`30 6 * * *`（毎朝 06:30 JST）を推奨**。タイムゾーンを Asia/Tokyo に
4. 実行プロンプト: `/morning-digest`
5. 保存

> **なぜ 06:30 JST か**: 予定本体は 7:00–7:30 に固定。データの鮮度を高めるため
> 収集はその直前に走らせます。実行には通常 1〜3 分かかり、Scheduled Trigger
> 起動には数分の遅延が乗ることもあるため、**7:00 まで 30 分弱の余裕**を
> 確保する `30 6 * * *` がバランス良好です。もっと攻めるなら `40 6 * * *`、
> 余裕を取るなら `15 6 * * *` などに調整してください。

詳細仕様: https://code.claude.com/docs/en/claude-code-on-the-web

> Scheduled Trigger 実行時のセッションでも、あなたの Claude アカウントに紐付いた Google Calendar MCP の認証が使われます。

---

## 編集ポイント

- **クライアント／業界**: `.claude/commands/morning-digest.md` の「kiCk の主要クライアントと所属業界」セクション
- **取り上げる分野**: 同ファイルの「ニュース収集の指示」セクション
- **HTML レイアウト**: 同ファイルの「予定の本文（description）の HTML 構成」セクション
- **予定の時間帯・タイトル**: 同ファイルの「カレンダー予定の作成」セクション

変更したら `git commit && git push` するだけで反映されます（GitHub Actions のような追加のデプロイ手順はなし）。

---

## 注意点

- **`WebSearch` ツールは米国（US）からのみ利用可能**です。Claude Code on the web のクラウド実行環境は通常 US 圏で稼働するため問題ありません。
- スケジュール実行は **Claude.ai のサブスクリプション枠内** で動くため、追加の従量課金は発生しません。
- Google Calendar MCP の認証が切れた場合は、Claude.ai の Settings → Integrations から再接続してください。
