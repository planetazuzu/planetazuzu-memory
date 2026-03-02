# Relations

## Mapa de Relaciones entre Proyectos

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SISTEMA IA DISTRIBUIDO                          │
│                     (brain/CONTEXTO.md)                            │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  ZEROCLAW    │     │   TALENTOS   │     │   CODECLAW    │
│ (reference)  │     │   (active)   │     │   (pending)   │
└───────────────┘     └───────────────┘     └───────────────┘
        ▲                                           │
        │                                           │
        └───────────────────┬───────────────────────┘
                            ▼
                ┌───────────────────────┐
                │   SYSTEM PROMPTS     │
                │      & AGENTS        │
                │    (agents/)         │
                └───────────────────────┘
```

## Dependencias

| Proyecto | Depende de | Descripción |
|----------|------------|-------------|
| **CodeClaw** | ZeroClaw | Basado en el runtime de ZeroClaw |
| **TalentOs** | - | Proyecto independiente (Next.js) |
| **Sistema IA** | CodeClaw, ZeroClaw, Agents | Orquestación de nodos |
| **System Prompts** | ZeroClaw, OpenCode | Configuración de agentes |

## Conexiones

### Sistema IA Distribuido → Nodos
- VPS (207.180.226.141) → Director
- HP G1 (192.168.1.139) → CTO/Infra
- RPi (pepper@pepper.local) → Marketing

### CodeClaw → Stack
- core-rust/ → Runtime Rust (ZeroClaw)
- channels/ → Canales comunicación
- mcp-servers/ → MCP servers
- mobile-android/ → App Android

### Agents → Tools
- prompt-unificado → 19 Skills
- TOOLS.md → SSH configs, nodos

## Ubicaciones

| Proyecto | Ruta local |
|----------|------------|
| CodeClaw | `/work/En Curso/codeclaw` |
| TalentOs | `/work/En Curso/TalentOs` |
| ZeroClaw | `/work/En Curso/codeclaw/packages/core-rust` |
| Brain | `/brain/` |
| Agents | `/agents/` |
| Memory | `/.memory/` |
