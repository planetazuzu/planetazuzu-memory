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
        │                                                   │
        │                                                   │
        └───────────────────┬───────────────────────────────┘
                            ▼
        ┌───────────────────────────────────────────────┐
        │           SYSTEM PROMPTS & AGENTS              │
        │                 (agents/)                    │
        └───────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────────┐
        │            GTS-REPO-GUARDIAN                   │
        │            (MCP - automation)                  │
        │    Controls: github.com/planetazuzu/*           │
        └───────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────────┐
        │         REPOSITORIO MEMORIA                    │
        │        (planetazuzu-memory)                    │
        │    Estado centralizado de proyectos             │
        └───────────────────────────────────────────────┘
```

## Dependencias

| Proyecto | Depende de | Descripción |
|----------|------------|-------------|
| **CodeClaw** | ZeroClaw | Basado en el runtime de ZeroClaw |
| **TalentOs** | - | Proyecto independiente (Next.js) |
| **Sistema IA** | CodeClaw, ZeroClaw, Agents | Orquestación de nodos |
| **System Prompts** | ZeroClaw, OpenCode | Configuración de agentes |
| **gts-repo-guardian** | GitHub API | MCP para gestión de repos |
| **planetazuzu-memory** | gts-repo-guardian | Memoria centralizada |

## Flujo de Trabajo

```
gts-repo-guardian (MCP)
    │
    ├── review_repository → Puntuación 0-100
    ├── generate_readme → README profesional
    ├── clean_repository → Estructura limpia
    ├── review_all_repositories → Informe global
    ├── apply_improvements → Mejoras automáticas
    └── watch_repositories → Monitorización
            │
            ▼
    Actualiza memoria → planetazuzu-memory
```

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

### gts-repo-guardian → Repos GitHub
- 15 repos públicos de @planetazuzu
- Revisión automática de calidad
- Generación de README profesional
- Limpieza y estructura

## Ubicaciones

| Proyecto | Ruta local | Repo GitHub |
|----------|------------|-------------|
| CodeClaw | `/work/En Curso/codeclaw` | - |
| TalentOs | `/work/En Curso/TalentOs` | - |
| ZeroClaw | `/work/En Curso/codeclaw/packages/core-rust` | - |
| Brain | `/brain/` | - |
| Agents | `/agents/` | - |
| Memory | `/.memory/` | github.com/planetazuzu/planetazuzu-memory |
| gts-repo-guardian | `/work/En Curso/gts-repo-guardian` | github.com/PlanetaZero/gts-repo-guardian |
| guia-tes-digital | - | github.com/planetazuzu/guia-tes-digital |
