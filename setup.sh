#!/bin/bash
# setup.sh - Miniflux RSS Stack セットアップスクリプト

set -e

echo "=== Miniflux RSS Stack セットアップ ==="
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cat > .env << EOF
# PostgreSQL設定
POSTGRES_USER=miniflux
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
POSTGRES_DB=miniflux

# Miniflux管理者アカウント
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Miniflux API設定（初回起動後に取得）
MINIFLUX_API_KEY=

# SMTP設定（ダイジェストメール用）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=your-email@gmail.com
SMTP_TO=recipient@example.com
EOF
    echo "✓ .env file created"
    echo
    echo "⚠️  重要: .envファイルを編集してSMTP設定を更新してください"
    echo
else
    echo "✓ .env file already exists"
fi

# Make scripts executable
chmod +x wait-for-api.sh 2>/dev/null || true
chmod +x bootstrap_feeds.py 2>/dev/null || true
chmod +x send_digest.py 2>/dev/null || true

# Start services
echo
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo
echo "Waiting for services to start..."
sleep 10

# Check if Miniflux is running
if curl -s -o /dev/null -w "%{http_code}" http://localhost:2222/healthcheck | grep -q "200"; then
    echo "✓ Miniflux is running"
else
    echo "✗ Miniflux is not responding. Check logs with: docker-compose logs miniflux"
    exit 1
fi

# Get API key if not set
source .env
if [ -z "$MINIFLUX_API_KEY" ]; then
    echo
    echo "=== APIキーの取得 ==="
    echo "1. ブラウザで http://localhost:2222 を開く"
    echo "2. 管理者アカウントでログイン:"
    echo "   Username: $ADMIN_USERNAME"
    echo "   Password: $ADMIN_PASSWORD"
    echo "3. Settings → API Keys → Create API Key"
    echo "4. 生成されたAPIキーを .env の MINIFLUX_API_KEY に設定"
    echo "5. docker-compose restart digest-cron で再起動"
    echo
    echo "Admin credentials saved to: admin-credentials.txt"
    cat > admin-credentials.txt << EOF
Miniflux Admin Credentials
==========================
URL: http://localhost:2222
Username: $ADMIN_USERNAME
Password: $ADMIN_PASSWORD

⚠️  このファイルは安全な場所に保管し、設定後は削除してください
EOF
fi

echo
echo "=== セットアップ完了 ==="
echo
echo "次のステップ:"
echo "1. .envファイルのSMTP設定を更新"
echo "2. APIキーを取得して.envに設定"
echo "3. bootstrap_feeds.pyでRSSフィードを登録"
echo
echo "例: docker-compose exec digest-cron python /app/bootstrap_feeds.py https://news.ycombinator.com"
echo
echo "ログの確認: docker-compose logs -f"