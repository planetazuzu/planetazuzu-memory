# Decisions

## 2026-03-02 (Servidor)

### D004: Stack del VPS Nexus

**Contexto:** Documentar el stack productivo del servidor

**Decisión:** Mantener servicios minimalistas con Docker

**Razón:**
- Docker aísla dependencias
- Easy backup/restore de volúmenes
- nginx como reverse proxy central

**Consecuencias:**
- 11 contenedores (todos detenidos para backup)
- 4 volúmenes persistentes
- Ollama con 3 modelos locales

---

### D005: OpenCode + OpenClaw en VPS

**Contexto:** Agentes IA en el servidor

**Decisión:** OpenCode como agente principal, OpenClaw para orquestación

**Razón:**
- OpenCode: asistencia general
- OpenClaw: gateway Telegram + WebSocket
- MCP servers: codeclaw_builder para CodeClaw

---

## 2026-03-02

### D001: Roadmap de 12 meses

**Contexto:** Necesidad de estructurar el desarrollo de CodeClaw desde cero

**Decisión:** Roadmap de 12 meses dividido en 4 fases

**Razón:**
- Fase 1 establece fundación sólida (CI/CD, core, seguridad)
- Fases progresivas añaden complejidad controlada
- Permite iteración y ajuste entre fases

**Consecuencias:**
- Total estimado: 480 días-hombre
- Milestones claros cada 3 meses

---

### D002: Stack tecnológico

**Contexto:** Proyecto existente con base ZeroClaw

**Decisión:** Mantener Rust + TypeScript/Node.js

**Razón:**
- ZeroClaw ya tiene arquitectura robusta en Rust
- TypeScript para flexibilidad en canales y herramientas
- Monorepo con pnpm + Turbo

---

### D003: Formato de documentación para IA

**Contexto:** Necesidad de que agentes IA lean el estado del proyecto

**Decisión:** Archivo de estado en .memory/projects/README.md con formato estructurado

**Razón:**
- Formato consistente y parseable
- metadata en JSON para machine-readable
- Tags para búsqueda
