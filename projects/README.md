# Project Status Registry

> **Última actualización:** 2026-03-02  
> **Formato:** AGENT-READABLE v1.0  
> **Ubicación:** `/home/planetazuzu/.memory/projects/`  
> **Para IAs:** Este archivo contiene el estado de TODOS los proyectos  

---

## Formato del Registro

Cada proyecto debe seguir esta estructura:

```markdown
## [NOMBRE]

- **Status:** [pending|active|completed|on-hold|archived]
- **Priority:** [P0|P1|P2|P3]
- **Start:** [YYYY-MM-DD]
- **End:** [YYYY-MM-DD or null]
- **Owner:** [owner or null]
- **Dependencies:** [list or null]

### Resumen
[Descripción corta en 1-2 oraciones]

### Tech Stack
- [lista de tecnologías]

### Roadmap
- [Fase actual o siguiente]

### metadata
```json
{
  "location": "ruta/del/proyecto",
  "docs": ["doc1.md", "doc2.md"],
  "contacts": ["usuario/equipo"],
  "tags": ["tag1", "tag2"]
}
```
```

---

## Proyectos Registrados

---

## CODECLAW

- **Status:** pending
- **Priority:** P0
- **Start:** 2026-03-02
- **End:** null
- **Owner:** planetazuzu
- **Dependencies:** null

### Resumen
Plataforma de agentes IA autónomos de alto rendimiento con múltiples canales de comunicación y herramientas extensibles. Monorepo con Rust (ZeroClaw-based) y TypeScript.

### Tech Stack
- **Runtime:** Rust (ZeroClaw-based)
- **Backend:** TypeScript / Node.js
- **Monorepo:** pnpm 9.0 + Turbo 2.0
- **Canales:** CLI, Telegram, WhatsApp, Web
- **MCP Servers:** Google, Files, Search, Code, Deploy
- **Mobile:** Kotlin / Jetpack Compose
- **Docs:** Markdown con i18n (en, zh-CN, ja, ru, fr, vi, el)

### Roadmap
El proyecto tiene un roadmap de 12 meses dividido en 4 fases:

| Fase | Timeline | Focus | Estado |
|------|----------|-------|--------|
| F1 | Meses 1-3 | Fundación (CI/CD, Core, Seguridad básica) | pending |
| F2 | Meses 4-6 | Expansión (Canales, Tools, Memoria) | pending |
| F3 | Meses 7-9 | Inteligencia (Agentes especializados, Código, Multi-agente) | pending |
| F4 | Meses 10-12 | Enterprise (Seguridad, Escalabilidad, Dashboard) | pending |

### Métricas Objetivo
- Code coverage: >70%
- Test pass rate: >95%
- Uptime: >99.9%
- Latencia p95: <500ms

### metadata
```json
{
  "location": "/home/planetazuzu/work/En Curso/codeclaw",
  "docs": [
    "DEVELOPMENT_PLAN.md",
    "docs/phase-1-fundacion.md",
    "docs/phase-2-expansion.md",
    "docs/phase-3-inteligencia.md",
    "docs/phase-4-enterprise.md",
    "packages/core-rust/docs/security-roadmap.md"
  ],
  "contacts": ["planetazuzu"],
  "tags": ["ia", "agents", "autonomous", "rust", "typescript", "monorepo"]
}
```

---

## ZEROCLAW (Referencia)

- **Status:** completed
- **Priority:** N/A
- **Start:** pre-2026
- **End:** 2026-02-13
- **Owner:** theonlyhennygod
- **Dependencies:** null

### Resumen
Runtime de agente autónomo en Rust que sirve como base tecnológica para CodeClaw. Versión 0.1.0 lançada con arquitectura trait-based modular.

### Tech Stack
- Rust
- SQLite (bundled)
- Trait-driven architecture

### metadata
```json
{
  "location": "/home/planetazuzu/work/En Curso/codeclaw/packages/core-rust",
  "docs": [
    "docs/README.md",
    "docs/security-roadmap.md",
    "AGENTS.md"
  ],
  "contacts": ["theonlyhennygod"],
  "tags": ["rust", "agent-runtime", "reference"]
}
```

---

## Próximos Pasos

1. [ ] Iniciar Fase 1: Fundación
2. [ ] Configurar CI/CD
3. [ ] Setup infraestructura inicial

---

## TALENTOS

- **Status:** active
- **Priority:** P0
- **Start:** 2025
- **End:** null
- **Owner:** planetazuzu
- **Dependencies:** null

### Resumen
Aplicación full-stack de gestión de recursos humanos y talento. Incluye módulo de empleados, nóminas, vacaciones, evaluación de desempeño y forum interno. Next.js con TypeScript.

### Tech Stack
- **Frontend:** Next.js 14, TypeScript, TailwindCSS
- **Backend:** Next.js API Routes
- **Database:** PostgreSQL (Supabase), SQLite (Dexie para local)
- **Auth:** NextAuth.js / Supabase Auth
- **State:** Zustand, Dexie (offline-first)

### Estado Actual
- ⚠️ ~30 errores TypeScript pendientes en archivos:
  - `dexie.ts` - Tipos de usuario y métodos
  - `postgres.ts` - Incompatibilidad de tipos
  - `supabase.ts` - Referencias undefined
- .env.production faltante (requerido para producción)

### metadata
```json
{
  "location": "/home/planetazuzu/work/En Curso/TalentOs",
  "docs": [],
  "contacts": ["planetazuzu"],
  "tags": ["nextjs", "hr", "talent-management", "typescript"]
}
```

---

## LIMPIEZA DE SISTEMA (2026-03-02)

- **Status:** completed
- **Priority:** N/A
- **Start:** 2026-03-02
- **End:** 2026-03-02
- **Owner:** planetazuzu
- **Dependencies:** null

### Resumen
Limpieza y reorganización del sistema de archivos. Todo lo no-core movido a /home/planetazuzu/workspace/. Contenedores Docker huérfanos eliminados. Proyectos core protegidos en carpetas originales.

### Tech Stack
- Docker, Docker Compose
- Linux (Pop!_OS)

### Problemas Identificados
1. **TalentOs:** Requiere `.env.production` (comportamiento normal de seguridad Node.js/Next.js)
2. **docker-compose:** Versión 1.29.2 con conflicto de bibliotecas (urllib3, requests)

### Recomendaciones
- Usar `docker compose` (sin guion) en lugar de `docker-compose`
- Revisar archivos `.env` faltantes antes de iniciar proyectos

### metadata
```json
{
  "location": "Sistema",
  "docs": [],
  "contacts": ["planetazuzu"],
  "tags": ["system", "cleanup", "docker"]
}
```

---

## SISTEMA IA DISTRIBUIDO (Red de Nodos)

- **Status:** active
- **Priority:** P1
- **Start:** 2026-02
- **End:** null
- **Owner:** planetazuzu
- **Dependencies:** null

### Resumen
Arquitectura de empresa IA autónoma distribuida en múltiples nodos/servidores.

### Nodos

| Nodo | Rol | IP | Estado | Servicios |
|------|-----|-----|--------|-----------|
| VPS | Director | 207.180.226.141 | ✅ Activo | Ollama, OpenClaw, Docker (Nextcloud, NPM, Portainer) |
| HP G1 | CTO/Infra | 192.168.1.139 | 🔧 Config | Ollama, OpenCode, OpenClaw |
| RPi | Marketing | pepper@pepper.local | ⏳ Pendiente | Ollama, OpenCode, OpenClaw |

### Carpetas Compartidas (VPS /shared/)
- `/memoria/` - Memoria central
- `/proyectos/` - Proyectos compartidos
- `/tareas/` - Cola de tareas
- `/resultados/` - Outputs de agentes
- `/config/` - Configuraciones

### Pendientes
1. Configurar SSH bidireccional entre nodos
2. Montar carpetas compartidas via SSHFS
3. Configurar comunicación entre agentes
4. Integración multi-agent en OpenClaw

### metadata
```json
{
  "location": "/home/planetazuzu/brain/",
  "docs": ["CONTEXTO.md", "memoria/2026-02-18-sistema-IA.md"],
  "contacts": ["planetazuzu"],
  "tags": ["distributed", "multi-node", "ia-autonoma", "vps", "raspberry-pi"]
}
```

---

## SYSTEM PROMPTS & AGENTS

- **Status:** active
- **Priority:** P1
- **Start:** 2026-02
- **End:** null
- **Owner:** planetazuzu
- **Dependencies:** null

### Resumen
Conjunto de archivos de configuración para agentes IA (OpenClaw, OpenCode). Incluye prompts unificados,tools, identidad y memoria.

### Archivos Incluidos

| Archivo | Descripción |
|---------|-------------|
| `prompt-unificado-opencode.md` | Server Monitor + 19 Skills para OpenClaw |
| `TOOLS.md` | Notes locales: SSH, nodos, TTS |
| `AGENTS.md` | Workspace config, memoria, heartbeats |
| `OPENCLAW_MULTIAGENT.md` | Config multiagente |
| `MEMORY.md` | Memoria a largo plazo |
| `USER.md` | Configuración de usuario |
| `SOUL.md` | Principios/identidad del agente |
| `IDENTITY.md` | Identidad |
| `HEARTBEAT.md` | Tareas periódicas |

### Ubicaciones
- `/home/planetazuzu/agents/` - Directorio principal
- `/home/planetazuzu/.zeroclaw/workspace/` - Workspace ZeroClaw

### metadata
```json
{
  "location": "/home/planetazuzu/agents/",
  "docs": ["prompt-unificado-opencode.md", "TOOLS.md", "AGENTS.md"],
  "contacts": ["planetazuzu"],
  "tags": ["agents", "openclaw", "opencode", "prompts", "system"]
}
```

---

## PROYECTOS EN DIRECTORIO

### work/proyectos/ (Proyectos Activos)
Total: ~64 proyectos en `/home/planetazuzu/work/proyectos/`

Algunos proyectos identificados:
- aid-contributor
- ambulance-iachat
- ambulancias / ambulancias-navarra
- app_gestion_vacaciones
- app-glasgow
- app_nominas
- chatopenia
- EMERMAPP
- flotas-app
- gts
- hrms
- memoai
- (lista completa en directorio)

### work/En Curso/
- `codeclaw/` - Plataforma agentes IA (pending)
- `TalentOs/` - Gestión RRHH (active, con errores TS)

### work/apps/
Directorio de aplicaciones

### work/Proyectos/
Proyectos adicionales

---

*Este archivo es leído por agentes IA para entender el estado de los proyectos.*
*Para añadir un nuevo proyecto, seguir el formato arriba.*
*Última actualización: 2026-03-02*
