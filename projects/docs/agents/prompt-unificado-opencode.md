# Prompt Unificado: Server Monitor + Skills OpenClaw

Tienes dos tareas. Hazlas en orden y espera mi confirmación entre ellas.

---

## TAREA 1 — Server Monitor Daemon (independiente)

Crea un daemon de monitorización de servidor completamente independiente. No depende de OpenCode ni de ninguna herramienta externa. Solo Node.js.

**Ubicación:** `/opt/server-monitor/`

**Estructura:**
```
/opt/server-monitor/
├── src/
│   ├── daemon.js          # Proceso principal
│   ├── cli.js             # Interfaz de terminal
│   ├── config.js          # Variables de entorno
│   ├── monitors/
│   │   ├── metrics.js     # CPU, memoria, disco, PostgreSQL
│   │   └── alerter.js     # Evaluación de umbrales
│   ├── cleaners/
│   │   └── cleaner.js     # Limpieza de logs, caché, Docker
│   └── notifications/
│       └── notifier.js    # Telegram + Email
├── install.sh             # Instalación systemd
├── package.json
├── .env.example
└── README.md
```

**Requisitos:**

1. **Monitorización** (cada 5 min, configurable):
   - CPU > 85% → alerta
   - Memoria RAM > 90% → alerta
   - Disco > 80% → alerta
   - PostgreSQL: si cae, conexiones > 80%, slow queries
   - Procesos zombie > 5 → aviso

2. **Notificaciones:**
   - Telegram bot (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
   - Email SMTP (SMTP_USER, SMTP_PASS, ALERT_EMAIL)
   - Cooldown 30 min entre alertas
   - Reporte diario a las 8:00 (silencioso)

3. **Limpieza** (dry-run por defecto, --force para ejecutar):
   - Logs > 30 días
   - Caché sistema (apt, /tmp, journal)
   - Procesos zombie
   - Imágenes Docker sin usar

4. **Comandos CLI** (`server-monitor`):
   - `status` → métricas con barras de color
   - `check` → health check completo
   - `logs` → errores recientes
   - `clean` → preview
   - `clean --force` → ejecutar
   - `test-notify` → probar notificaciones

5. **install.sh** debe:
   - Verificar Node.js 18+
   - Copiar a /opt/server-monitor/
   - Crear servicio systemd /etc/systemd/system/
   - Crear comando global /usr/local/bin/
   - Generar .env desde .env.example

Cuando termines TAREA 1, muéstrame el resultado y espera mi OK.

---

## TAREA 2 — Instalar 19 Skills en OpenClaw

Copia las 19 skills a `/usr/lib/node_modules/openclaw/skills/`.

**Formato exacto para cada SKILL.md:**

```markdown
---
name: [nombre-skill]
description: |
  [Descripción de cuándo activar]
license: MIT
compatibility: opencode
metadata:
  audience: [audiencia]
  workflow: [flujo]
---

# Título

[Contenido...]
```

**Las 19 skills a crear:**

1. **ultrabrain** - Razonamiento profundo, arquitectura, DDD, sistemas distribuidos, CQRS, patrones de decisión, análisis de trade-offs. 5 fases: entender problema real → descomponer → generar 3+ alternativas → evaluar con criterios → recomendar con condiciones.

2. **visual-engineering** - 5 pilares: design systems (tokens 3 capas), CSS escalable (utility-first, container queries), motion con intención (productive vs expresivo), accesibilidad WCAG 2.1, performance visual (Core Web Vitals).

3. **devdocs** - README, CONTRIBUTING, CHANGELOG (Keep a Changelog), API REST docs con tablas, diagramas Mermaid, runbooks. Principios: pirámide de información.

4. **task-automation** - Guías de estilo, scaffolding (NestJS, Next.js), plantillas (componentes, hooks, endpoints, tests), Conventional Commits.

5. **workflow-integration** - Git workflows (trunk-based, release, hotfix), migraciones sin downtime (expand-contract), CI/CD (GitHub Actions), Terraform, Docker multistage, secrets OIDC.

6. **context-injection** - Protocolo 5 pasos: orientación estructural → schema datos → contratos API → ADRs → ejemplos código.

7. **role-based-access** - Permisos allow/ask/deny. 5 perfiles: frontend, backend, platform, docs, reviewer.

8. **tool-extension** - MCP servers: PostgreSQL, GitHub, Slack, Brave Search. Crear MCP servers personalizados TypeScript.

9. **specialized-formatting** - Framework Diátaxis (tutorial/how-to/reference/explanation), español España vs LATAM, British vs American English, estilos código (AirBnB, Google, PEP8), Conventional Commits.

10. **code-review** - 6 etiquetas: BLOCKER, MAJOR, MINOR, NIT, SUGGESTION, QUESTION. 6 categorías: corrección, seguridad, rendimiento, mantenibilidad, tests, consistencia. Checklist pre-PR.

11. **onboarding** - Setup local paso a paso, mapa del codebase, plan primera semana, guía del equipo, checklist accesos.

12. **security-audit** - OWASP Top 10: broken access control, fallos criptográficos (bcrypt vs MD5), injection (SQL/command/path), misconfiguration, authentication failures, secrets expuestos. Herramientas: gitleaks.

13. **api-design** - REST/GraphQL/tRPC. Paginación cursor vs offset, RFC 9457, versionado, webhooks con firma e idempotencia.

14. **performance-profiling** - Clinic.js, flame graphs, memory leaks, pg_stat_statements, EXPLAIN ANALYZE, bundle analysis, Core Web Vitals.

15. **database-design** - Dominio vs UI, formas normales, tipos correctos (dinero céntimos, TIMESTAMPTZ), índices, CTE recursiva, soft delete, expand-contract.

16. **prompt-engineering** - System prompt 6 secciones, few-shot examples, chain-of-thought, structured outputs, gestión contexto, pipeline RAG, evals con juez LLM.

17. **agent-orchestration** - Pipeline secuencial, fan-out/fan-in paralelo, agentes especializados. PROJECT_STATE.md compartido.

18. **tech-debt-tracker** - 6 tipos de deuda, registro con campos, puntuación (Impacto×3 + Urgencia×2 + Facilidad×1), informe trimestral.

19. **project-memory** - Proyectos en Markdown. Stack, decisiones, arquitectura, relaciones. Nunca borra.

**Proceso:**
1. Verifica que `/usr/lib/node_modules/openclaw/skills/` existe
2. Crea carpeta + SKILL.md para cada skill
3. Incluye el contenido completo (no resúmenes)
4. Verifica: `ls /usr/lib/node_modules/openclaw/skills/`

---

## Reglas generales

- Si algo falla, dime antes de continuar
- Cada tarea = un commit con mensaje
- Si necesitas sudo para /usr/lib/, úsalo
- Skills = contenido completo

**Ejecuta TAREA 1 primero. Espera OK. Luego TAREA 2.**
