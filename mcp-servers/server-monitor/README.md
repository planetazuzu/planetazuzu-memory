# Server Monitor Daemon

A standalone server monitoring daemon built with Node.js 18+.

## Features

- **System Metrics**: CPU, Memory, Disk, Swap
- **Process Monitoring**: Zombie process detection
- **Database Monitoring**: PostgreSQL availability, connections, slow queries
- **Docker Monitoring**: Container status
- **Port Monitoring**: Listening network ports
- **Notifications**: Telegram bot and Email (SMTP)
- **Auto-cleanup**: Logs, cache, Docker resources
- **Daily Reports**: Automatic summary at 8:00 AM

## Installation

```bash
cd /opt/server-monitor
chmod +x install.sh
sudo ./install.sh
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
nano .env
```

### Required Variables

**Telegram (optional but recommended):**
- `TELEGRAM_BOT_TOKEN` - Get from @BotFather
- `TELEGRAM_CHAT_ID` - Your chat ID

**Email (optional):**
- `SMTP_HOST` - SMTP server
- `SMTP_PORT` - Usually 587
- `SMTP_USER` - Username
- `SMTP_PASS` - Password
- `ALERT_EMAIL` - Destination email

**PostgreSQL (optional):**
- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_NAME` - Database name
- `DB_USER` - Database user

### Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `THRESHOLD_CPU` | 85 | Alert if CPU > 85% |
| `THRESHOLD_MEM` | 90 | Alert if Memory > 90% |
| `THRESHOLD_DISK` | 80 | Alert if Disk > 80% |
| `THRESHOLD_SWAP` | 50 | Warn if Swap > 50% |
| `THRESHOLD_ZOMBIES` | 5 | Warn if > 5 zombies |
| `THRESHOLD_DB_CONNECTIONS` | 80 | Alert if > 80% connections |

### Timing

| Variable | Default | Description |
|----------|---------|-------------|
| `CHECK_INTERVAL` | 300000 | Check every 5 minutes |
| `ALERT_COOLDOWN` | 1800000 | 30 min between same alerts |
| `DAILY_REPORT_HOUR` | 8 | Daily report at 8:00 AM |

## Usage

```bash
server-monitor status       # Show metrics with colored bars
server-monitor check        # Run health check
server-monitor logs         # Show recent system logs
server-monitor clean       # Preview cleanup (dry run)
server-monitor clean --force # Execute cleanup
server-monitor test-notify # Test notifications
server-monitor alert "msg" # Send manual alert

server-monitor daemon start  # Start daemon
server-monitor daemon stop   # Stop daemon
server-monitor daemon restart # Restart daemon
```

## Service Management

```bash
systemctl start server-monitor
systemctl stop server-monitor
systemctl restart server-monitor
systemctl status server-monitor
systemctl enable server-monitor  # Auto-start on boot
```

## Log Location

- Alerts: `/var/log/server-monitor/alerts.log`
- Daemon logs: `journalctl -u server-monitor -f`

## Alert Cooldown

Alerts of the same type are only sent once per 30 minutes (configurable) to prevent spam.

## Daily Reports

At 8:00 AM (configurable), a silent report is sent with system status. No alerts are triggered, just information.

## Cleanup

The cleaner can:
- Remove logs older than 30 days
- Clean apt cache
- Clean /tmp files older than 7 days
- Vacuum journal logs
- Clean zombie processes (SIGCHLD to parent)
- Prune Docker containers, images, volumes, networks

By default cleanup runs in dry-run mode. Use `--force` to execute.
