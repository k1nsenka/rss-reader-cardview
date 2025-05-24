# Miniflux RSS Reader Stack

自己ホスト型のRSSリーダーシステム。Minifluxをベースに、カスタムカードスタイルテーマと毎日のダイジェストメール機能を提供します。

## 機能

- **Miniflux RSS Reader**: 最新版のMinifluxとPostgreSQLデータベース
- **カスタムカードテーマ**: モダンなカードスタイルのUI（ダークモード対応）
- **自動フィード登録**: URLからRSSフィードを自動検出して購読
- **毎日のダイジェストメール**: 毎朝6:30（JST）に重要な記事をメール送信
- **カテゴリ分類**: papers、tech、businessの3カテゴリに自動分類
- **注目度スコアリング**: スター、ブックマーク、新しさを基に記事をランク付け

## クイックスタート

```bash
# リポジトリのクローン
git clone <repository-url>
cd miniflux-rss-stack

# セットアップスクリプトの実行
chmod +x setup.sh
./setup.sh
```

## 手動セットアップ

### 1. 環境変数の設定

`.env`ファイルを作成し、以下の変数を設定：

```bash
# PostgreSQL設定
POSTGRES_USER=miniflux
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=miniflux

# Miniflux管理者アカウント
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password

# Miniflux API設定（初回起動後に取得）
MINIFLUX_API_KEY=your-api-key

# SMTP設定（ダイジェストメール用）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=your-email@gmail.com
SMTP_TO=recipient@example.com
```

### 2. 起動

```bash
# wait-for-api.shに実行権限を付与
chmod +x wait-for-api.sh

# サービスの起動
docker-compose up -d

# ログの確認
docker-compose logs -f
```

### 3. APIトークンの作成

1. http://localhost:2222 にアクセス
2. 管理者アカウントでログイン
3. Settings → API Keys → Create API Key
4. 生成されたAPIキーを`.env`の`MINIFLUX_API_KEY`に設定
5. `docker-compose restart digest-cron`で再起動

### 4. RSSフィードの登録

```bash
# 単一URLから自動検出
docker-compose exec digest-cron python /app/bootstrap_feeds.py https://news.ycombinator.com

# 複数URLを一度に登録
docker-compose exec digest-cron python /app/bootstrap_feeds.py \
  https://arxiv.org \
  https://techcrunch.com \
  https://www.bloomberg.com
```

推奨フィード：
- **Tech**: https://news.ycombinator.com, https://techcrunch.com, https://www.theverge.com
- **Papers**: https://arxiv.org, https://www.nature.com, https://www.science.org
- **Business**: https://www.bloomberg.com, https://www.reuters.com, https://www.ft.com

## カスタマイズ

### テーマのカスタマイズ

`miniflux-theme-card.css`を編集してテーマをカスタマイズできます。変更後は以下で反映：

```bash
docker-compose restart miniflux
```

### ダイジェストメールの設定

`send_digest.py`で以下を調整可能：

- `WEIGHT_STARS`, `WEIGHT_BOOKMARKS`, `WEIGHT_RECENCY`: 注目度スコアの重み
- `TOP_N_PER_CATEGORY`: カテゴリごとの表示記事数（デフォルト: 5）
- `EMAIL_TEMPLATE`: メールテンプレート

### カテゴリマッピング

`bootstrap_feeds.py`の`CATEGORY_MAPPINGS`を編集して、ドメインとカテゴリの対応を変更できます。

### Cronスケジュール

ダイジェストメールの送信時刻を変更するには、`Dockerfile`内のcron設定を編集：

```dockerfile
# 例: 毎朝8:00に変更
RUN echo "0 8 * * * cd /app && /usr/bin/python3 /app/send_digest.py >> /var/log/cron.log 2>&1" > /etc/crontabs/root
```

## Gmail SMTP設定

Gmailを使用する場合は、以下の手順でアプリパスワードを生成：

1. Googleアカウントの2段階認証を有効化
2. https://myaccount.google.com/apppasswords にアクセス
3. 「メール」を選択してアプリパスワードを生成
4. 生成されたパスワードを`SMTP_PASS`に設定

## トラブルシューティング

### ダイジェストメールが送信されない

```bash
# Cronログの確認
docker-compose logs digest-cron

# 手動実行でテスト
docker-compose exec digest-cron python /app/send_digest.py

# SMTP設定の確認
docker-compose exec digest-cron env | grep SMTP
```

### フィードの登録に失敗する

```bash
# APIキーの確認
docker-compose exec digest-cron env | grep MINIFLUX_API_KEY

# API接続テスト
docker-compose exec digest-cron python -c "
import requests, os
headers = {'X-Auth-Token': os.environ.get('MINIFLUX_API_KEY')}
r = requests.get('http://miniflux:8080/v1/me', headers=headers)
print(r.status_code, r.text)
"
```

### Minifluxにアクセスできない

```bash
# サービスの状態確認
docker-compose ps

# Minifluxのログ確認
docker-compose logs miniflux

# ヘルスチェック
curl http://localhost:2222/healthcheck
```

### データベース接続エラー

```bash
# PostgreSQLの状態確認
docker-compose exec postgres pg_isready -U miniflux

# データベースの再起動
docker-compose restart postgres miniflux
```

## バックアップとリストア

### バックアップ

```bash
# データベースのバックアップ
docker-compose exec postgres pg_dump -U miniflux miniflux > backup_$(date +%Y%m%d).sql

# ボリューム全体のバックアップ
docker run --rm -v miniflux-postgres-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/miniflux-backup-$(date +%Y%m%d).tar.gz /data
```

### リストア

```bash
# データベースのリストア
docker-compose exec -T postgres psql -U miniflux miniflux < backup_20240101.sql

# ボリュームのリストア
docker run --rm -v miniflux-postgres-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/miniflux-backup-20240101.tar.gz -C /
```

## セキュリティ推奨事項

1. **強力なパスワード**: すべてのパスワードは推測困難なものを使用
2. **APIキーの保護**: `.env`ファイルは絶対にGitにコミットしない
3. **ネットワーク分離**: 本番環境では適切なファイアウォール設定を実施
4. **HTTPS対応**: 公開する場合はリバースプロキシでHTTPS化
5. **定期的な更新**: Dockerイメージを定期的に更新

```bash
# イメージの更新
docker-compose pull
docker-compose up -d
```

## 開発とデバッグ

```bash
# コンテナ内でシェルを起動
docker-compose exec digest-cron /bin/sh

# Pythonインタラクティブシェル
docker-compose exec digest-cron python

# リアルタイムログ監視
docker-compose logs -f --tail=100
```

## アンインストール

```bash
# サービスの停止と削除
docker-compose down

# ボリュームも含めて完全削除（データが失われます）
docker-compose down -v

# イメージの削除
docker rmi $(docker images -q miniflux*)
```

## ライセンス

このプロジェクトはMIT Licenseで公開されています。Minifluxは Apache License 2.0 でライセンスされています。