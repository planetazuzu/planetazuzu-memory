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
