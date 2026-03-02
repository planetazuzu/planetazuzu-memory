# Stack

## CodeClaw (2026-03-02)

### Runtime
- **Core Runtime:** Rust (ZeroClaw-based)
- **Backend:** TypeScript / Node.js
- **Monorepo:** pnpm 9.0 + Turbo 2.0

### Packages
- `packages/core/` - Core logic (TypeScript)
- `packages/core-rust/` - Agent runtime en Rust (ZeroClaw)
- `packages/channels/` - Communication channels
  - `cli/` - Command-line interface
  - `telegram/` - Telegram bot
  - `whatsapp/` - WhatsApp integration
  - `web/` - Web interface
  - `web-v2/` - New web interface
- `packages/mcp-servers/` - MCP servers
  - `google/` - Google services
  - `files/` - File operations
  - `search/` - Search capabilities
  - `code/` - Code execution
  - `deploy/` - Deployment tools
- `packages/mobile-android/` - Android app
- `packages/shared/` - Shared utilities

### Documentación
- Markdown con i18n
- Idiomas: en, zh-CN, ja, ru, fr, vi, el

---

## VPS Nexus (Servidor Productivo)

### Sistema
- **OS:** Linux (Debian/Ubuntu)
- **Host:** vmi2782086 (Hetzner)
- **IP:** 207.180.226.141
- **Tailscale:** 100.84.169.7

### Runtime
- **Docker:** containerd + Docker Engine
- **Python:** 3.x (servicios, nexus-monitor, alert-hub)
- **Node.js:** 22.x (OpenCode MCP, server-monitor)
- **Ollama:** Modelos IA locales

### Servicios
| Servicio | Descripción |
|----------|-------------|
| nexus-monitor | Monitor VPS (Python, puerto 31435) |
| alert-hub | Bot notificaciones Telegram |
| server-monitor-mcp | MCP para OpenCode |
| OpenClaw Gateway | ws://127.0.0.1:18789 |
| webhook-deploy | Receptor webhooks |

### Contenedores Docker
- Nextcloud (app + mariadb)
- Portainer
- Nginx Proxy Manager
- blackbox (api + postgres + redis)
- nexus-dashboard
- openclaw-sandbox

### Modelos Ollama
- qwen3:8b (5.2 GB)
- mistral:latest (4.4 GB)
- llama3.2:3b (2.0 GB)
