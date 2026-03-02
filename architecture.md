# Architecture

## CodeClaw (2026-03-02)

### Visión General
Plataforma de agentes IA autónomos de alto rendimiento

### Capas Principales

```
codeclaw-monorepo/
├── packages/
│   ├── core/              # Core logic (TypeScript)
│   ├── core-rust/        # Agent runtime (Rust) - ZeroClaw
│   ├── channels/         # Communication channels
│   │   ├── cli/
│   │   ├── telegram/
│   │   ├── whatsapp/
│   │   ├── web/
│   │   └── web-v2/
│   ├── mcp-servers/      # MCP servers
│   │   ├── google/
│   │   ├── files/
│   │   ├── search/
│   │   ├── code/
│   │   └── deploy/
│   ├── mobile-android/   # Android app
│   └── shared/           # Shared utilities
```

### Patrones Arquitectura

- **Trait-based:** Extensión via implementaciones de traits
- **Factory:** Registro de providers/channels/tools via factories
- **Layered:** Separación clara de responsabilidades
- **Plugin:** Sistema de plugins para extensiones

### Extensibilidad (Puntos de entrada)

| Punto | Trait | Localización |
|-------|-------|--------------|
| Providers | `Provider` | `src/providers/traits.rs` |
| Channels | `Channel` | `src/channels/traits.rs` |
| Tools | `Tool` | `src/tools/traits.rs` |
| Memory | `Memory` | `src/memory/traits.rs` |
| Observability | `Observer` | `src/observability/traits.rs` |
| Runtime | `RuntimeAdapter` | `src/runtime/traits.rs` |
| Peripherals | `Peripheral` | `src/peripherals/traits.rs` |

### Referencias
- ZeroClaw: runtime base en Rust
- LangChain: abstracciones de IA
- MCP: Model Context Protocol
- FastAPI: patterns de API
