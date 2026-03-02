#!/bin/bash

set -e

echo "=========================================="
echo "  Server Monitor Installation"
echo "=========================================="

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

echo ""
echo "Step 1: Checking Node.js version..."
NODE_VERSION=$(node -v 2>/dev/null | sed 's/v//' | cut -d. -f1)
if [ -z "$NODE_VERSION" ] || [ "$NODE_VERSION" -lt 18 ]; then
  echo "❌ Node.js 18+ is required. Current version: $(node -v)"
  exit 1
fi
echo "✅ Node.js $(node -v) detected"

echo ""
echo "Step 2: Creating directory structure..."
mkdir -p /opt/server-monitor
mkdir -p /var/log/server-monitor
echo "✅ Directories created"

echo ""
echo "Step 3: Installing dependencies..."
cd /opt/server-monitor
npm install --silent 2>/dev/null || npm install
echo "✅ Dependencies installed"

echo ""
echo "Step 4: Creating .env from template..."
if [ ! -f /opt/server-monitor/.env ]; then
  cp /opt/server-monitor/.env.example /opt/server-monitor/.env
  echo "✅ .env created from template"
  echo "   Please edit /opt/server-monitor/.env with your settings"
else
  echo "⚠️  .env already exists, skipping"
fi

echo ""
echo "Step 5: Creating systemd service..."
cat > /etc/systemd/system/server-monitor.service << 'EOF'
[Unit]
Description=Server Monitor Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/server-monitor
ExecStart=/usr/bin/node /opt/server-monitor/src/daemon.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "✅ Systemd service created"

echo ""
echo "Step 6: Creating global command..."
chmod +x /opt/server-monitor/src/cli.js
chmod +x /opt/server-monitor/src/daemon.js
ln -sf /opt/server-monitor/src/cli.js /usr/local/bin/server-monitor
echo "✅ Global command installed: server-monitor"

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit /opt/server-monitor/.env with your Telegram/SMTP settings"
echo "2. Run: server-monitor test-notify  (to verify notifications)"
echo "3. Run: server-monitor daemon start (to start the daemon)"
echo "4. Run: systemctl enable server-monitor (for auto-start on boot)"
echo ""
echo "Available commands:"
echo "  server-monitor status       - Show metrics with colored bars"
echo "  server-monitor check        - Run health check"
echo "  server-monitor logs         - Show recent system logs"
echo "  server-monitor clean        - Preview cleanup"
echo "  server-monitor clean --force - Execute cleanup"
echo "  server-monitor test-notify  - Test notifications"
echo "  server-monitor daemon start - Start daemon"
echo ""
