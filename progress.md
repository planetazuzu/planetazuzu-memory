# Progress

## 2026-03-02 (Servidor Nexus)

### Inventario y Backup

**Realizado:**
- Parar todos los contenedores Docker (sin eliminar datos)
- Backup completo en `/root/BACKUP_PRE_FORMAT_20260302_1252/`
- Archivo final: `BACKUP_PRE_FORMAT_FINAL.tar.gz` (728K)

**Archivos incluidos en backup:**
- Puertos abiertos (ss -lntp)
- docker ps -a, images, volumes
- systemctl list-units running
- Repos git encontrados
- Top 50 procesos RAM/CPU
- Configs: /root/.config/opencode, /root/.openclaw
- docker-compose.yml encontrados
- Volúmenes Docker documentados

---

### Configuración OpenCode/OpenClaw

**Skills disponibles en servidor:**
- 23 skills en /root/.config/opencode/skills/
- MCP: codeclaw_builder (/root/codeclaw_builder_mcp.py)

**Configuración actual:**
```json
{
  "mcpServers": {
    "codeclaw_builder": {
      "command": "python3",
      "args": ["/root/codeclaw_builder_mcp.py"]
    }
  }
}
```

---

### TalentOS (del AGENTS.md)

**Estado:** Fase 1 92% completada
- **Ubicación:** /var/www/proyectos/TalentOs/
- **Framework:** Next.js 15 + TypeScript + Tailwind
- **Arquitectura:** Multi-tenant SaaS

**Características:**
- DBProvider: Dexie (local) + PostgreSQL (servidor)
- Genkit para IA (Google Gemini)
- LTI 1.3 + SCORM 2004
- RGPD/ARCO compliant
- Shadcn/ui

---

## 2026-03-02

### Limpieza de Sistema

**Realizado:**
- Limpieza completa del sistema de archivos
- Todo lo no-core movido a `/home/planetazuzu/workspace/`
- Contenedores Docker huérfanos eliminados
- Proyectos core protegidos en carpetas originales

**Problemas técnicos encontrados:**
1. **TalentOs**: Falta `.env.production` (normal en Next.js)
2. **docker-compose**: Versión 1.29.2 con conflicto urllib3/requests

**Recomendación:** Usar `docker compose` (sin guion)

---

### CodeClaw - Setup Inicial

**Acciones realizadas:**

1. **Carga de skills** - Se cargaron 24 skills de opencode para el proyecto

2. **Análisis del proyecto existente:**
   - Exploración del monorepo en `/home/planetazuzu/work/En Curso/codeclaw`
   - Identificación de packages: core, core-rust, channels, mcp-servers, mobile-android, shared
   - Revisión del roadmap de seguridad existente (security-roadmap.md)

3. **Plan de desarrollo creado:**
   - DEVELOPMENT_PLAN.md - Plan principal con visión, roadmap 12 meses, métricas
   - docs/phase-1-fundacion.md - Detalle F1 (90 días)
   - docs/phase-2-expansion.md - Detalle F2 (110 días)
   - docs/phase-3-inteligencia.md - Detalle F3 (145 días)
   - docs/phase-4-enterprise.md - Detalle F4 (135 días)

4. **Registro de proyecto en memoria:**
   - .memory/projects/README.md - Estado de proyectos legible por IA

**Roadmap establecido:**
- Fase 1 (Meses 1-3): Fundación - CI/CD, Core Framework, Seguridad básica
- Fase 2 (Meses 4-6): Expansión - Canales adicionales, Herramientas, Memoria
- Fase 3 (Meses 7-9): Inteligencia - Agentes especializados, Código, Multi-agente
- Fase 4 (Meses 10-12): Enterprise - Seguridad avanzada, Escalabilidad, Dashboard

**Próximo paso:** Iniciar implementación de Fase 1

---

### Sistema IA Distribuido - Actualización

**Estado actual de nodos:**

| Nodo | IP | Estado |
|------|-----|--------|
| VPS (Director) | 207.180.226.141 | ✅ Activo |
| HP G1 (CTO) | 192.168.1.139 | 🔧 Config |
| RPi (Marketing) | pepper@pepper.local | ⏳ Pendiente |

**Servicios en cada nodo:**
- Ollama (modelos IA)
- OpenClaw (agente autónomo)
- OpenCode (asistente IA)
- Docker (VPS: Nextcloud, NPM, Portainer)

**Pendientes:**
- SSH entre nodos
- Carpetas compartidas /shared
- Comunicación inter-agentes

---

## 2026-03-02 (continuación)

### gts-repo-guardian - MCP Creado

**Realizado:**
- Creación de servidor MCP completo para gestión de repos GitHub
- Ubicación: `/home/planetazuzu/work/En Curso/gts-repo-guardian/`
- Stack: TypeScript + Node.js + GitHub API

**Archivos creados:**
- `src/index.ts` - Servidor MCP principal
- `src/tools/review.ts` - Revisión de repos con puntuación 0-100
- `src/tools/readme.ts` - Generación automática de README
- `src/tools/clean.ts` - Limpieza y estructura
- `src/tools/batch.ts` - Revisión masiva
- `src/tools/improve.ts` - Aplicar mejoras automáticamente
- `src/tools/monitor.ts` - Monitorización continua
- `src/config/rules.ts` - Reglas de calidad
- `src/config/profiles.ts` - Configuración de perfiles
- `src/templates/readme-sanitario.md` - Template sanitario
- `src/templates/readme-tech.md` - Template tech
- `src/templates/readme-lab.md` - Template lab
- `.env.example` - Variables de entorno
- `README.md` - Documentación

**Funcionalidades implementadas:**
1. `review_repository` - Analiza repo y da puntuación 0-100
2. `generate_readme` - Genera README profesional
3. `clean_repository` - Limpia y estructura
4. `review_all_repositories` - Revisión masiva
5. `apply_improvements` - Aplica mejoras
6. `watch_repositories` - Monitoriza repos

---

### guia-tes-digital - README Actualizado

**Realizado:**
- Actualización de README con estándar GTS
- Repo: https://github.com/planetazuzu/guia-tes-digital

**Secciones añadidas:**
- ✅ Advertencia clínica
- ✅ Protocolos de referencia (ILCOR, ERC, SEMICYUC, SEMES)
- ✅ Aviso legal
- ✅ Cómo contribuir para TES
- ✅ Ecosistema de apps sanitarias
- ✅ Autor actualizado con LinkedIn

---

### Repositorios GitHub - Estado Actual

**Públicos:** 15 repositorios

Procesados:
- ✅ guia-tes-digital (actualizado)

Pendientes de procesar:
- app-glsgow
- rioja-ambulancias-mapa-pwa
- ia-primeros-auxilios
- app-P10
- salvaia
- revision_ambulancia
- revision_ambulancia1
- rioja-emergencia
- salva-primeros-ia-espa
- chat-api
- informe-asistencias

---

### Memoria de Proyectos - Actualizada

**Registros añadidos:**
- GTS-REPO-GUARDIAN (completed)
- REPOSITORIO MEMORIA (active)

**Repositorios dokumentados:**
- CodeClaw (pending)
- TalentOs (active)
- ZeroClaw (completed)
- Sistema IA Distribuido (active)
- GTS-REPO-GUARDIAN (completed)
- 15 repositorios públicos de @planetazuzu

---

## Antes de 2026-03-02

- Proyecto ZeroClaw base completado (v0.1.0 - 2026-02-13)
- Arquitectura trait-based establecida
- Múltiples canales y providers implementados
- Sistema de empresa IA distribuida concebido
- TalentOs en desarrollo con errores TypeScript (~30 errores)
