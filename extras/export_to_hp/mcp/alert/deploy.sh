#!/bin/bash
# AlertHub Deploy Script

set -e

echo "🚀 Deploying AlertHub..."

# Config
APP_DIR="/root/alert_hub"
PORT=31436
LOG_FILE="/var/log/alert_hub.log"
SERVICE_NAME="alert-hub"

# Install dependencies if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install --break-system-packages -q fastapi uvicorn httpx python-telegram-bot google-auth pydantic python-dotenv
fi

# Stop existing instance
echo "🛑 Stopping existing instance..."
pkill -f "uvicorn server:app" 2>/dev/null || true
sleep 1

# Create log directory
mkdir -p "$(dirname $LOG_FILE)"
touch $LOG_FILE

# Start the service
echo "▶️  Starting AlertHub..."
cd $APP_DIR
nohup python3 -m uvicorn server:app --host 0.0.0.0 --port $PORT >> $LOG_FILE 2>&1 &
sleep 2

# Verify
if ss -tlnp | grep -q ":$PORT "; then
    echo "✅ AlertHub is running on port $PORT"
    curl -s http://localhost:$PORT/health
else
    echo "❌ Failed to start AlertHub"
    tail -20 $LOG_FILE
    exit 1
fi

echo "🎉 Deploy complete!"
