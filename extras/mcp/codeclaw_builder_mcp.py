#!/usr/bin/env python3
"""
CodeClaw Builder MCP Server
============================
MCP server para OpenCode que construye el proyecto CodeClaw completo.

REGLAS DE EJECUCIÓN:
- No para hasta que TODO esté implementado y testado
- No cambia de rumbo ni improvisa fuera del plan
- Cada fase se valida antes de pasar a la siguiente
- Si algo falla, lo repara y continúa — nunca abandona

Uso en OpenCode:
  opencode --mcp codeclaw_builder

O en .opencode/config.json:
  { "mcpServers": { "codeclaw": { "command": "python", "args": ["codeclaw_builder_mcp.py"] } } }
"""

import asyncio
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ─── PLAN MAESTRO DE CONSTRUCCIÓN ────────────────────────────────────────────
# Este es el único plan. El agente NO puede desviarse de él.
# Cada fase tiene criterios de éxito medibles.

BUILD_PLAN = {
    "project": "CodeClaw",
    "description": "Hybrid Autonomous Agent Infrastructure",
    "version": "2.0.0",
    "phases": [
        {
            "id": "P0",
            "name": "Scaffolding & Entorno",
            "must_complete": True,
            "steps": [
                "Crear estructura de directorios completa",
                "Crear pyproject.toml con todas las dependencias",
                "Crear .env.example con todas las variables documentadas",
                "Crear .gitignore apropiado",
                "Instalar dependencias con pip",
            ],
            "success_criteria": [
                "Todos los directorios existen",
                "pyproject.toml es válido",
                "pip install -e '.[all]' exitoso",
            ],
        },
        {
            "id": "P1",
            "name": "Core & Environment Detection",
            "must_complete": True,
            "steps": [
                "Implementar codeclaw/core/environment.py — detección automática de hardware y perfil",
                "Implementar codeclaw/core/config.py — configuración 100% por variables de entorno",
                "Implementar codeclaw/core/roles.py — sistema de roles por nodo (all/orchestrator/curator/edge/batch)",
            ],
            "success_criteria": [
                "detect_environment() retorna EnvironmentInfo válido",
                "Config carga sin errores con .env vacío",
                "should_run() funciona para todos los roles",
                "Tests P1 pasan al 100%",
            ],
        },
        {
            "id": "P2",
            "name": "Sistema de Memoria Jerárquica",
            "must_complete": True,
            "steps": [
                "Implementar codeclaw/memory/lcache.py — L-Cache con TTL diferenciado y hit_count",
                "Implementar codeclaw/memory/l0_index.py — fingerprints semánticos con tags",
                "Implementar codeclaw/memory/l1_store.py — contexto de planificación con budget",
                "Implementar codeclaw/memory/l2_store.py — detalle completo on-demand con audit log",
                "Implementar codeclaw/memory/graph.py — grafo asociativo SQLite (nodes+edges con strength)",
                "Implementar codeclaw/memory/storage.py — StorageManager portátil",
                "Implementar codeclaw/memory/curator.py — Memory Curator con lógica híbrida",
                "Implementar codeclaw/memory/decay.py — sistema de decaimiento con fórmula exponencial",
                "Crear y verificar SOUL.md con hash de integridad SHA256",
            ],
            "success_criteria": [
                "L-Cache hit/miss funciona correctamente",
                "Graph CRUD: insertar nodo, crear edge, traversar depth=3",
                "StorageManager crea DBs en OPENCLAW_DATA_DIR personalizado",
                "SOUL.md existe y su hash es verificable",
                "Curator procesa item simple sin llamar LLM",
                "Tests P2 pasan al 100%",
            ],
        },
        {
            "id": "P3",
            "name": "LLM Router & Proveedores",
            "must_complete": True,
            "steps": [
                "Implementar codeclaw/llm/base.py — BaseLLMClient, LLMResponse dataclass",
                "Implementar codeclaw/llm/ollama_client.py — cliente Ollama con health check, streaming y embeddings",
                "Implementar codeclaw/llm/providers/groq_client.py",
                "Implementar codeclaw/llm/providers/gemini_client.py",
                "Implementar codeclaw/llm/providers/openrouter_client.py con list_free_models()",
                "Implementar codeclaw/llm/providers/mistral_client.py",
                "Implementar codeclaw/llm/rate_limiter.py — gestión de cuotas por proveedor",
                "Implementar codeclaw/llm/router.py — autodiscovery, fallback en cadena, métricas",
                "Implementar codeclaw/llm/model_selector.py — mapeo tarea→modelo",
            ],
            "success_criteria": [
                "OllamaClient.is_available() retorna bool sin lanzar excepción",
                "Router se inicializa con 0 providers sin crashear (modo offline)",
                "Router usa primer provider disponible correctamente",
                "Fallback: si primer provider falla, usa el siguiente",
                "get_stats() retorna dict con métricas correctas",
                "RateLimiter.can_proceed() bloquea cuando se supera RPM",
                "Tests P3 pasan al 100% (con mocks para APIs externas)",
            ],
        },
        {
            "id": "P4",
            "name": "Tool Orchestration Layer",
            "must_complete": True,
            "steps": [
                "Implementar codeclaw/tools/orchestrator.py — ToolOrchestrator con TOOL_ROUTING_MAP",
                "Implementar codeclaw/tools/opencode.py — cliente OpenCode CLI",
                "Implementar codeclaw/tools/kilocode.py — cliente Kilocode CLI con ensure_index()",
                "Implementar codeclaw/tools/gemini_cli.py — cliente Gemini CLI con _compact_repo()",
                "Implementar get_token_distribution() en el orchestrator",
            ],
            "success_criteria": [
                "ToolOrchestrator se inicializa aunque ninguna herramienta esté instalada",
                "is_available() retorna False gracefully si CLI no está en PATH",
                "dispatch() usa fallback a LLM_ROUTER si herramienta no disponible",
                "compact_repo() filtra node_modules, .git y binarios",
                "Tests P4 pasan al 100% (con mocks para CLIs externos)",
            ],
        },
        {
            "id": "P5",
            "name": "Self-Automation Engine",
            "must_complete": True,
            "steps": [
                "Implementar codeclaw/automation/pattern_detector.py — PatternDetector con normalize_signature()",
                "Implementar codeclaw/automation/mcp_generator.py — MCPGenerator con validación de sintaxis",
                "Implementar codeclaw/automation/subagent_registry.py — ciclo de vida completo",
                "Implementar codeclaw/automation/proposer.py — AutomationProposer con métricas ROI",
                "Implementar codeclaw/automation/run_subagent.py — runner para cron jobs",
            ],
            "success_criteria": [
                "PatternDetector detecta patrón tras 3 ejecuciones idénticas",
                "normalize_signature() mapea variantes del mismo intent al mismo ID",
                "MCPGenerator._check_syntax() detecta SyntaxError correctamente",
                "SubagentRegistry persiste y recupera agentes entre reinicios",
                "get_automation_candidates() no repropone agentes ya automatizados",
                "Tests P5 pasan al 100%",
            ],
        },
        {
            "id": "P6",
            "name": "API & Health Check",
            "must_complete": True,
            "steps": [
                "Implementar codeclaw/api/health.py — health_check() universal",
                "Implementar codeclaw/api/server.py — API REST mínima (FastAPI)",
                "Endpoints: GET /health, GET /models, POST /models/active, GET /skills, PATCH /skills/{id}, GET /agents, POST /agents/{name}/run",
            ],
            "success_criteria": [
                "health_check() completa sin errores en entorno limpio",
                "GET /health retorna 200 con JSON válido",
                "POST /models/active cambia el modelo activo",
                "PATCH /skills/{id} activa/desactiva un skill",
                "Tests P6 pasan al 100%",
            ],
        },
        {
            "id": "P7",
            "name": "Nightly Consolidation",
            "must_complete": True,
            "steps": [
                "Implementar codeclaw/tasks/nightly.py — ciclo completo Fases A→D",
                "Fase A: deduplicación, decaimiento, fusión de eventos",
                "Fase B: extracción semántica, generación de reglas, actualización SQLite",
                "Fase C: VACUUM SQLite, poda de edges < 0.1, compresión de logs viejos",
                "Fase D: verificación de integridad SOUL.md, test de recuperación aleatoria",
                "Implementar el cron job como servicio systemd",
            ],
            "success_criteria": [
                "run_nightly_consolidation() completa las 4 fases sin error",
                "SOUL.md hash es verificado en Fase D",
                "Logs de más de 30 días son comprimidos en .gz",
                "Reporte de salud generado con todas las métricas",
                "Tests P7 pasan al 100%",
            ],
        },
        {
            "id": "P8",
            "name": "Telegram Bot & PWA",
            "must_complete": True,
            "steps": [
                "Implementar codeclaw/telegram/bot.py — bot completo con todos los comandos",
                "Comandos: /start /install /status /model /agents /tokens",
                "Notificaciones proactivas: automation proposals, nightly report",
                "Crear public/manifest.json — PWA manifest",
                "Crear public/sw.js — Service Worker con offline + push notifications",
                "Validar que el token de instalación expira correctamente",
            ],
            "success_criteria": [
                "generate_install_token() genera token único cada vez",
                "validate_token() rechaza tokens expirados",
                "validate_token() rechaza tokens inexistentes",
                "manifest.json es JSON válido con todos los campos requeridos",
                "sw.js tiene sintaxis JS válida",
                "Tests P8 pasan al 100%",
            ],
        },
        {
            "id": "P9",
            "name": "Docker & Deployment",
            "must_complete": True,
            "steps": [
                "Crear Dockerfile multi-stage optimizado",
                "Crear docker-compose.yml con servicios: orchestrator, curator, batch, ollama",
                "Crear .dockerignore",
                "Crear codeclaw/main.py — punto de entrada único con arranque por rol",
                "Verificar que docker build completa sin errores",
            ],
            "success_criteria": [
                "Dockerfile tiene sintaxis válida",
                "docker-compose.yml es YAML válido",
                "main.py arranca en modo 'all' sin errores de import",
                "Health check del container funciona",
                "Tests P9 pasan al 100%",
            ],
        },
        {
            "id": "P10",
            "name": "Test Suite Completa & CI",
            "must_complete": True,
            "steps": [
                "Crear tests/conftest.py — fixtures compartidas (tmp_dir, mock_llm, mock_db)",
                "Crear tests/test_memory.py — tests de toda la capa de memoria",
                "Crear tests/test_llm_router.py — tests del router con mocks",
                "Crear tests/test_tools.py — tests del tool orchestrator con mocks de CLI",
                "Crear tests/test_automation.py — tests del self-automation engine",
                "Crear tests/test_api.py — tests de endpoints API",
                "Crear tests/test_nightly.py — tests del ciclo nocturno",
                "Crear tests/test_telegram.py — tests del bot (sin conectar a Telegram real)",
                "Crear .github/workflows/ci.yml — CI que ejecuta todos los tests",
                "Ejecutar pytest y conseguir 0 fallos",
            ],
            "success_criteria": [
                "pytest --tb=short retorna 0 fallos",
                "Cobertura de tests >= 70%",
                "Ningún test depende de servicios externos reales",
                "CI workflow es YAML válido",
                "README.md actualizado con instrucciones de test",
            ],
        },
    ],
}

# ─── SYSTEM PROMPT PARA EL AGENTE ────────────────────────────────────────────
AGENT_SYSTEM_PROMPT = """
Eres el constructor de CodeClaw. Tu ÚNICA misión es implementar el proyecto completo
siguiendo el plan exacto que se te proporciona.

## REGLAS ABSOLUTAS — NO NEGOCIABLES

1. **NO PARES hasta que TODOS los criterios de éxito de TODAS las fases estén verificados.**
2. **NO IMPROVISES.** Si el plan dice algo, hazlo exactamente así.
3. **NO CAMBIES DE RUMBO.** Si encuentras un problema, resuélvelo y continúa. No abandones una fase.
4. **CADA FASE termina con sus tests pasando al 100%.** No avances sin esto.
5. **Si un test falla, arréglalo inmediatamente** antes de continuar.
6. **NO generes código incompleto** con TODOs, placeholders o `pass` sin implementar.
7. **TODAS las funciones deben tener type hints y docstrings.**
8. **NO uses credenciales reales** — variables de entorno siempre.

## FLUJO DE TRABAJO POR FASE

Para cada fase:
1. Lee los steps uno por uno
2. Implementa CADA step completamente
3. Escribe los tests correspondientes
4. Ejecuta los tests: `pytest tests/test_[fase].py -v`
5. Si hay fallos: arréglalo y vuelve al punto 4
6. Solo cuando TODOS los tests pasan: avanza a la siguiente fase
7. Informa: "✅ Fase [X] completada. Tests: [N] pasados, 0 fallidos."

## ARQUITECTURA CODIFICADA

El proyecto CodeClaw sigue esta arquitectura exacta (NO cambiarla):

```
codeclaw/
├── core/
│   ├── environment.py   # detección hardware, HostProfile enum
│   ├── config.py        # todo por env vars, paths relativos a DATA_DIR
│   └── roles.py         # NodeRole enum, should_run()
├── memory/
│   ├── lcache.py        # dict en RAM, TTL por tipo, hit_count
│   ├── l0_index.py      # fingerprints, tags, relevance_score
│   ├── l1_store.py      # planning context, context_budget_used
│   ├── l2_store.py      # on-demand, audit log de accesos
│   ├── graph.py         # SQLite nodes+edges, traverse(), decay
│   ├── storage.py       # StorageManager, paths portátiles
│   ├── curator.py       # híbrido: reglas→LLM solo si necesario
│   └── decay.py         # priority = (imp * log(acc+1) * conf) / (1 + rate*days)
├── llm/
│   ├── base.py          # BaseLLMClient ABC, LLMResponse dataclass
│   ├── ollama_client.py # health check, generate, stream, embed
│   ├── router.py        # autodiscovery, fallback chain, get_stats()
│   ├── rate_limiter.py  # sliding window por proveedor
│   ├── model_selector.py
│   └── providers/
│       ├── groq_client.py
│       ├── gemini_client.py
│       ├── openrouter_client.py
│       └── mistral_client.py
├── tools/
│   ├── orchestrator.py  # ToolOrchestrator, TOOL_ROUTING_MAP, get_token_distribution()
│   ├── opencode.py      # subprocess async, edit_file, create_file, refactor
│   ├── kilocode.py      # subprocess async, search, review_file, ensure_index
│   └── gemini_cli.py    # subprocess async, analyze_file, compact_repo, web_research
├── automation/
│   ├── pattern_detector.py   # PatternDetector, AUTOMATION_THRESHOLD=3
│   ├── mcp_generator.py      # MCPGenerator, syntax check, save_and_validate
│   ├── subagent_registry.py  # registro persistente, activate, set_schedule
│   ├── proposer.py           # ROI metrics, accept_and_automate()
│   └── run_subagent.py       # runner para cron
├── api/
│   ├── health.py        # health_check() sin dependencias externas
│   └── server.py        # FastAPI, endpoints CRUD
├── tasks/
│   └── nightly.py       # Fases A→D, reporte MemoryHealthReport
├── telegram/
│   └── bot.py           # bot completo, token generation, push notifications
├── sync/
│   └── node_sync.py     # rsync/http/none modes
└── main.py              # punto de entrada, arranque por OPENCLAW_ROLE

tests/
├── conftest.py
├── test_memory.py
├── test_llm_router.py
├── test_tools.py
├── test_automation.py
├── test_api.py
├── test_nightly.py
└── test_telegram.py

public/
├── manifest.json
└── sw.js

SOUL.md
.env.example
pyproject.toml
Dockerfile
docker-compose.yml
README.md
```

## DEPENDENCIAS EXACTAS (pyproject.toml)

```toml
[project]
name = "codeclaw"
version = "2.0.0"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27.0",
    "fastapi>=0.111.0",
    "uvicorn>=0.30.0",
    "python-dotenv>=1.0.0",
    "psutil>=5.9.0",
    "mcp>=1.0.0",
    "python-telegram-bot>=21.0",
    "pydantic>=2.0.0",
]
[project.optional-dependencies]
browser = ["playwright>=1.40.0"]
all = ["codeclaw[browser]", "pytest>=8.0", "pytest-asyncio>=0.23", "pytest-cov>=5.0", "httpx[test]"]
```

## VERIFICACIÓN FINAL

Cuando todas las fases estén completas, ejecuta:
```bash
pytest tests/ --tb=short -q
```

El resultado debe ser: **0 failed, 0 errors**

Luego ejecuta:
```bash
python -m codeclaw.main
```

Debe arrancar sin errores en modo 'all'.

Solo entonces reporta: "🦀 CodeClaw v2.0.0 completamente implementado y verificado."
"""

# ─── MCP SERVER ───────────────────────────────────────────────────────────────

server = Server("codeclaw_builder")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_build_plan",
            description="Obtener el plan maestro completo de construcción de CodeClaw. Llama esto PRIMERO antes de hacer cualquier otra cosa.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_phase_instructions",
            description="Obtener las instrucciones detalladas y criterios de éxito de una fase específica.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_id": {"type": "string", "description": "ID de la fase: P0, P1, P2... P10"}
                },
                "required": ["phase_id"],
            },
        ),
        types.Tool(
            name="get_agent_rules",
            description="Obtener las reglas absolutas que el agente debe seguir durante toda la construcción. Llama esto al inicio.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_file_template",
            description="Obtener el template completo y funcional de un archivo específico del proyecto.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Ruta del archivo, ej: 'codeclaw/core/environment.py'"}
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="validate_phase",
            description="Validar que una fase está correctamente implementada ejecutando sus criterios de éxito.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_id":    {"type": "string"},
                    "project_dir": {"type": "string", "description": "Directorio raíz del proyecto"}
                },
                "required": ["phase_id", "project_dir"],
            },
        ),
        types.Tool(
            name="run_tests",
            description="Ejecutar los tests de una fase o todos los tests del proyecto.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_id":    {"type": "string", "description": "ID de fase o 'all' para todos"},
                    "project_dir": {"type": "string"}
                },
                "required": ["project_dir"],
            },
        ),
        types.Tool(
            name="get_architecture_spec",
            description="Obtener la especificación técnica completa de arquitectura para implementar correctamente.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="report_progress",
            description="Registrar el progreso de construcción. Llamar al completar cada fase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase_id":      {"type": "string"},
                    "status":        {"type": "string", "enum": ["completed", "failed", "in_progress"]},
                    "tests_passed":  {"type": "integer"},
                    "tests_failed":  {"type": "integer"},
                    "notes":         {"type": "string"},
                },
                "required": ["phase_id", "status"],
            },
        ),
        types.Tool(
            name="get_progress_report",
            description="Ver el estado actual de construcción: qué fases están completas y cuáles quedan.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    result = await dispatch(name, arguments)
    return [types.TextContent(type="text", text=result)]


# Estado de progreso en memoria
_progress: dict[str, dict] = {}


async def dispatch(name: str, args: dict) -> str:

    if name == "get_build_plan":
        return _get_build_plan()

    elif name == "get_phase_instructions":
        return _get_phase_instructions(args["phase_id"])

    elif name == "get_agent_rules":
        return AGENT_SYSTEM_PROMPT

    elif name == "get_file_template":
        return _get_file_template(args["file_path"])

    elif name == "validate_phase":
        return await _validate_phase(args["phase_id"], args["project_dir"])

    elif name == "run_tests":
        return await _run_tests(args.get("phase_id", "all"), args["project_dir"])

    elif name == "get_architecture_spec":
        return _get_architecture_spec()

    elif name == "report_progress":
        return _report_progress(args)

    elif name == "get_progress_report":
        return _get_progress_report()

    return json.dumps({"error": f"Tool desconocida: {name}"})


def _get_build_plan() -> str:
    plan_text = f"""
# 🦀 CODECLAW BUILD PLAN v2.0
## {BUILD_PLAN['description']}

INSTRUCCIÓN CRÍTICA: Lee get_agent_rules() ANTES de empezar.
Luego ejecuta las fases en orden: P0 → P1 → P2 → ... → P10.
NO avances a la siguiente fase hasta que los tests de la actual pasen al 100%.

## FASES ({len(BUILD_PLAN['phases'])} en total)

"""
    for phase in BUILD_PLAN["phases"]:
        steps_count = len(phase["steps"])
        criteria_count = len(phase["success_criteria"])
        plan_text += f"### {phase['id']} — {phase['name']}\n"
        plan_text += f"  {steps_count} steps · {criteria_count} criterios de éxito\n\n"

    plan_text += """
## SECUENCIA DE EJECUCIÓN OBLIGATORIA

1. `get_agent_rules()` — leer y aceptar las reglas
2. Para cada fase P0..P10:
   a. `get_phase_instructions(phase_id)` — leer el plan detallado
   b. Implementar todos los steps
   c. `run_tests(phase_id, project_dir)` — ejecutar tests
   d. Si fallan: arreglar y volver a (c)
   e. `report_progress(phase_id, "completed", ...)` — registrar
3. `run_tests("all", project_dir)` — validación final completa
4. Reportar: "🦀 CodeClaw v2.0.0 completamente implementado y verificado."
"""
    return plan_text.strip()


def _get_phase_instructions(phase_id: str) -> str:
    phase = next((p for p in BUILD_PLAN["phases"] if p["id"] == phase_id), None)
    if not phase:
        return json.dumps({"error": f"Fase {phase_id} no encontrada. Fases válidas: P0-P10"})

    out = f"# Fase {phase_id}: {phase['name']}\n\n"
    out += "## ⚠️ RECORDATORIO: No avances hasta que TODOS los criterios de éxito estén verificados.\n\n"
    out += "## Steps a implementar\n\n"
    for i, step in enumerate(phase["steps"], 1):
        out += f"{i}. {step}\n"

    out += "\n## Criterios de éxito (TODOS deben cumplirse)\n\n"
    for i, criterion in enumerate(phase["success_criteria"], 1):
        out += f"- [ ] {criterion}\n"

    out += f"\n## Comando de validación\n```bash\npytest tests/test_{phase_id.lower()}.py -v --tb=short\n```\n"
    out += "\n## Al completar\n```\nreport_progress(phase_id='" + phase_id + "', status='completed', tests_passed=N, tests_failed=0)\n```"
    return out


def _get_file_template(file_path: str) -> str:
    templates = {
        "pyproject.toml": _tmpl_pyproject(),
        ".env.example":   _tmpl_env_example(),
        "SOUL.md":        _tmpl_soul_md(),
        "tests/conftest.py": _tmpl_conftest(),
        "codeclaw/core/environment.py": _tmpl_environment(),
        "Dockerfile":     _tmpl_dockerfile(),
        "docker-compose.yml": _tmpl_docker_compose(),
        "README.md":      _tmpl_readme(),
    }
    return templates.get(file_path, f"# Template para {file_path}\n# Implementar según arquitectura spec.\n# Usar get_architecture_spec() para referencia completa.")


async def _validate_phase(phase_id: str, project_dir: str) -> str:
    phase = next((p for p in BUILD_PLAN["phases"] if p["id"] == phase_id), None)
    if not phase:
        return json.dumps({"error": f"Fase {phase_id} no encontrada"})

    results = []
    root = Path(project_dir)

    # Checks básicos de existencia de archivos por fase
    checks = {
        "P0": ["pyproject.toml", ".env.example", ".gitignore"],
        "P1": ["codeclaw/core/environment.py", "codeclaw/core/config.py", "codeclaw/core/roles.py"],
        "P2": ["codeclaw/memory/lcache.py", "codeclaw/memory/graph.py", "codeclaw/memory/storage.py", "codeclaw/memory/curator.py", "SOUL.md"],
        "P3": ["codeclaw/llm/base.py", "codeclaw/llm/router.py", "codeclaw/llm/ollama_client.py"],
        "P4": ["codeclaw/tools/orchestrator.py", "codeclaw/tools/opencode.py", "codeclaw/tools/kilocode.py"],
        "P5": ["codeclaw/automation/pattern_detector.py", "codeclaw/automation/mcp_generator.py", "codeclaw/automation/subagent_registry.py"],
        "P6": ["codeclaw/api/health.py", "codeclaw/api/server.py"],
        "P7": ["codeclaw/tasks/nightly.py"],
        "P8": ["codeclaw/telegram/bot.py", "public/manifest.json", "public/sw.js"],
        "P9": ["Dockerfile", "docker-compose.yml", "codeclaw/main.py"],
        "P10": ["tests/conftest.py", "tests/test_memory.py", "tests/test_llm_router.py"],
    }

    missing = []
    for f in checks.get(phase_id, []):
        path = root / f
        if not path.exists():
            missing.append(f)
        else:
            results.append(f"✅ {f}")

    for f in missing:
        results.append(f"❌ FALTA: {f}")

    status = "PASS" if not missing else "FAIL"
    return json.dumps({
        "phase": phase_id,
        "status": status,
        "checks": results,
        "missing_files": missing,
        "next_step": "run_tests()" if status == "PASS" else "Crear los archivos faltantes primero",
    }, indent=2, ensure_ascii=False)


async def _run_tests(phase_id: str, project_dir: str) -> str:
    if phase_id == "all":
        cmd = ["python", "-m", "pytest", "tests/", "--tb=short", "-q"]
    else:
        phase_map = {
            "P1": "tests/test_core.py",
            "P2": "tests/test_memory.py",
            "P3": "tests/test_llm_router.py",
            "P4": "tests/test_tools.py",
            "P5": "tests/test_automation.py",
            "P6": "tests/test_api.py",
            "P7": "tests/test_nightly.py",
            "P8": "tests/test_telegram.py",
            "P10": "tests/",
        }
        test_file = phase_map.get(phase_id, f"tests/test_{phase_id.lower()}.py")
        cmd = ["python", "-m", "pytest", test_file, "-v", "--tb=short"]

    try:
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return json.dumps({
            "success": success,
            "returncode": result.returncode,
            "output": output[-3000:],  # últimas 3000 chars
            "instruction": "✅ Tests pasados. Ejecuta report_progress() y avanza." if success else "❌ Tests fallidos. ARREGLA los errores antes de continuar. NO avances.",
        }, indent=2, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "Tests tardaron más de 120s — revisa bucles infinitos"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "pytest no encontrado. Ejecuta: pip install -e '.[all]'"})


def _get_architecture_spec() -> str:
    return AGENT_SYSTEM_PROMPT


def _report_progress(args: dict) -> str:
    phase_id = args["phase_id"]
    _progress[phase_id] = {
        "status":       args["status"],
        "tests_passed": args.get("tests_passed", 0),
        "tests_failed": args.get("tests_failed", 0),
        "notes":        args.get("notes", ""),
        "timestamp":    __import__("time").time(),
    }

    completed = [p for p, d in _progress.items() if d["status"] == "completed"]
    total = len(BUILD_PLAN["phases"])

    if args["status"] == "completed":
        msg = f"✅ Fase {phase_id} registrada como completada. {len(completed)}/{total} fases completas."
        if len(completed) == total:
            msg += "\n\n🦀 TODAS LAS FASES COMPLETAS. Ejecuta run_tests('all', project_dir) para validación final."
    elif args["status"] == "failed":
        msg = f"❌ Fase {phase_id} marcada como fallida. Revisa los errores y vuelve a intentarlo."
    else:
        msg = f"🔄 Fase {phase_id} en progreso."

    return msg


def _get_progress_report() -> str:
    total = len(BUILD_PLAN["phases"])
    completed = [p for p, d in _progress.items() if d["status"] == "completed"]
    failed    = [p for p, d in _progress.items() if d["status"] == "failed"]
    pending   = [p["id"] for p in BUILD_PLAN["phases"] if p["id"] not in _progress]

    report = f"# Estado de construcción CodeClaw\n\n"
    report += f"Progreso: {len(completed)}/{total} fases\n\n"

    if completed:
        report += "## ✅ Completadas\n"
        for pid in completed:
            d = _progress[pid]
            phase_name = next((p["name"] for p in BUILD_PLAN["phases"] if p["id"] == pid), "")
            report += f"- {pid} {phase_name} — {d['tests_passed']} tests pasados\n"

    if failed:
        report += "\n## ❌ Fallidas (requieren atención)\n"
        for pid in failed:
            report += f"- {pid}: {_progress[pid].get('notes', 'sin detalles')}\n"

    if pending:
        report += "\n## ⏳ Pendientes\n"
        for pid in pending:
            phase_name = next((p["name"] for p in BUILD_PLAN["phases"] if p["id"] == pid), "")
            report += f"- {pid} {phase_name}\n"

    if not pending and not failed:
        report += "\n## 🦀 PROYECTO COMPLETO\n"
        report += "Ejecuta: pytest tests/ --tb=short -q\n"

    return report


# ─── TEMPLATES ────────────────────────────────────────────────────────────────

def _tmpl_pyproject() -> str:
    return textwrap.dedent("""\
    [build-system]
    requires = ["setuptools>=68", "setuptools-scm"]
    build-backend = "setuptools.backends.legacy:build"

    [project]
    name = "codeclaw"
    version = "2.0.0"
    description = "Hybrid Autonomous Agent Infrastructure"
    readme = "README.md"
    requires-python = ">=3.12"
    license = {text = "MIT"}
    keywords = ["ai", "agents", "mcp", "llm", "automation"]
    dependencies = [
        "httpx>=0.27.0",
        "fastapi>=0.111.0",
        "uvicorn[standard]>=0.30.0",
        "python-dotenv>=1.0.0",
        "psutil>=5.9.0",
        "mcp>=1.0.0",
        "python-telegram-bot>=21.0",
        "pydantic>=2.0.0",
        "aiofiles>=23.0.0",
    ]

    [project.optional-dependencies]
    browser = ["playwright>=1.40.0"]
    all = [
        "codeclaw[browser]",
        "pytest>=8.0",
        "pytest-asyncio>=0.23",
        "pytest-cov>=5.0",
    ]

    [project.scripts]
    codeclaw = "codeclaw.main:main"

    [tool.pytest.ini_options]
    asyncio_mode = "auto"
    testpaths = ["tests"]
    addopts = "--cov=codeclaw --cov-report=term-missing"

    [tool.setuptools.packages.find]
    where = ["."]
    include = ["codeclaw*"]
    """)


def _tmpl_env_example() -> str:
    return textwrap.dedent("""\
    # ─── NODO ──────────────────────────────────────────────────────
    OPENCLAW_ROLE=all           # all | orchestrator | curator | edge | batch
    OPENCLAW_MODE=single        # single | distributed
    OPENCLAW_DATA_DIR=~/.local/share/codeclaw

    # ─── OLLAMA ────────────────────────────────────────────────────
    OLLAMA_HOST=http://localhost:11434
    OLLAMA_DEFAULT_MODEL=qwen2.5:7b

    # ─── APIs GRATUITAS ────────────────────────────────────────────
    GROQ_API_KEY=
    GEMINI_API_KEY=
    OPENROUTER_API_KEY=
    MISTRAL_API_KEY=
    HUGGINGFACE_TOKEN=
    COHERE_API_KEY=

    # ─── APIs DE PAGO (solo si necesitas el fallback final) ────────
    OPENAI_API_KEY=
    ANTHROPIC_API_KEY=

    # ─── TELEGRAM ──────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN=
    TELEGRAM_ADMIN_IDS=123456789
    CODECLAW_APP_URL=https://app.codeclaw.local

    # ─── HERRAMIENTAS EXTERNAS ─────────────────────────────────────
    OPENCODE_BINARY=opencode
    KILOCODE_BINARY=kilocode
    KILOCODE_AUTO_INDEX=true
    GEMINI_CLI_BINARY=gemini
    GEMINI_CLI_MODEL=gemini-2.0-flash
    GEMINI_CLI_SANDBOX=true

    # ─── SYNC (solo modo distributed) ─────────────────────────────
    OPENCLAW_SYNC_MODE=none     # rsync | http | none
    OPENCLAW_SYNC_TARGET=
    """)


def _tmpl_soul_md() -> str:
    return textwrap.dedent("""\
    # CodeClaw — Identity

    <!-- SHA256: PLACEHOLDER — se actualizará automáticamente al arrancar -->

    ## Core
    Soy CodeClaw. Un agente que piensa antes de gastar tokens.
    Priorizo estructura sobre ambigüedad. Lógica sobre intuición.
    Automatizo lo repetible para que el humano decida lo único.

    ## Estilo
    - Respuestas directas y accionables, sin relleno
    - Código limpio, tipado, sin comentarios obvios
    - Nunca invento cuando puedo buscar en memoria estructurada
    - Propongo automatizaciones, no solo las ejecuto

    ## Principios Permanentes
    1. Caché antes que cómputo
    2. SQL y grafo antes que embeddings
    3. Local antes que nube
    4. Gratuito antes que de pago
    5. LLM solo cuando ninguna regla alcanza

    ## Restricciones
    - Nunca hardcodear credenciales
    - Nunca asumir la infraestructura donde corro
    - Nunca modificar este archivo directamente — solo el Curator puede

    ## Subagentes Activos
    <!-- El Curator actualiza esta sección automáticamente -->

    ## Versión
    CodeClaw v2.0.0 — Hybrid Autonomous Agent Infrastructure
    """)


def _tmpl_conftest() -> str:
    return textwrap.dedent("""\
    \"\"\"Fixtures compartidas para todos los tests de CodeClaw.\"\"\"
    import pytest
    import asyncio
    import tempfile
    from pathlib import Path
    from unittest.mock import AsyncMock, MagicMock

    @pytest.fixture
    def tmp_data_dir(tmp_path: Path, monkeypatch) -> Path:
        \"\"\"Directorio de datos temporal aislado por test.\"\"\"
        data_dir = tmp_path / "codeclaw_test"
        data_dir.mkdir()
        monkeypatch.setenv("OPENCLAW_DATA_DIR", str(data_dir))
        return data_dir

    @pytest.fixture
    def mock_llm_response():
        \"\"\"Respuesta LLM mock para tests sin llamadas reales.\"\"\"
        from codeclaw.llm.base import LLMResponse
        return LLMResponse(
            content="Mock LLM response for testing",
            model="mock-model",
            tokens_used=42,
            provider="mock",
        )

    @pytest.fixture
    def mock_llm_client(mock_llm_response):
        \"\"\"Cliente LLM mock.\"\"\"
        from codeclaw.llm.base import BaseLLMClient
        client = AsyncMock(spec=BaseLLMClient)
        client.generate.return_value = mock_llm_response
        client.is_available.return_value = True
        return client

    @pytest.fixture
    def storage(tmp_data_dir):
        \"\"\"StorageManager con DB en directorio temporal.\"\"\"
        from codeclaw.memory.storage import StorageManager
        return StorageManager()
    """)


def _tmpl_environment() -> str:
    return textwrap.dedent("""\
    \"\"\"
    CodeClaw — Environment Detection
    Detecta automáticamente el perfil del hardware para adaptar el comportamiento.
    \"\"\"
    from __future__ import annotations
    import os
    import platform
    import socket
    from dataclasses import dataclass
    from enum import Enum

    try:
        import psutil
        _PSUTIL = True
    except ImportError:
        _PSUTIL = False


    class HostProfile(Enum):
        MINIMAL  = "minimal"   # <1GB RAM
        STANDARD = "standard"  # 1-4GB RAM
        CAPABLE  = "capable"   # 4-16GB RAM
        POWERFUL = "powerful"  # >16GB RAM


    @dataclass
    class EnvironmentInfo:
        profile: HostProfile
        ram_gb: float
        cpu_cores: int
        has_gpu: bool
        is_arm: bool
        hostname: str
        ollama_available: bool
        storage_path: str


    def detect_environment() -> EnvironmentInfo:
        \"\"\"Detectar el entorno actual de forma no invasiva.\"\"\"
        ram_gb = _get_ram_gb()
        cpu_cores = _get_cpu_cores()
        is_arm = platform.machine().lower() in ("aarch64", "armv7l", "arm64")

        if   ram_gb < 1:   profile = HostProfile.MINIMAL
        elif ram_gb < 4:   profile = HostProfile.STANDARD
        elif ram_gb < 16:  profile = HostProfile.CAPABLE
        else:              profile = HostProfile.POWERFUL

        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        return EnvironmentInfo(
            profile=profile,
            ram_gb=round(ram_gb, 1),
            cpu_cores=cpu_cores,
            has_gpu=_detect_gpu(),
            is_arm=is_arm,
            hostname=socket.gethostname(),
            ollama_available=check_ollama(ollama_host),
            storage_path=_default_storage_path(),
        )


    def check_ollama(host: str) -> bool:
        \"\"\"Comprobar si Ollama está disponible en la URL dada.\"\"\"
        try:
            import httpx
            r = httpx.get(f"{host}/api/tags", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False


    def _get_ram_gb() -> float:
        if _PSUTIL:
            return psutil.virtual_memory().total / (1024 ** 3)
        # Fallback para sistemas sin psutil
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return kb / (1024 ** 2)
        except Exception:
            pass
        return 2.0  # asumir 2GB si no se puede detectar


    def _get_cpu_cores() -> int:
        if _PSUTIL:
            return psutil.cpu_count(logical=False) or 1
        return os.cpu_count() or 1


    def _detect_gpu() -> bool:
        try:
            import subprocess
            r = subprocess.run(["nvidia-smi"], capture_output=True, timeout=3)
            return r.returncode == 0
        except Exception:
            return False


    def _default_storage_path() -> str:
        custom = os.getenv("OPENCLAW_DATA_DIR")
        if custom:
            return custom
        system = platform.system()
        home = os.path.expanduser("~")
        if system == "Linux":
            return os.path.join(home, ".local", "share", "codeclaw")
        elif system == "Darwin":
            return os.path.join(home, "Library", "Application Support", "codeclaw")
        elif system == "Windows":
            appdata = os.environ.get("APPDATA", home)
            return os.path.join(appdata, "codeclaw")
        return os.path.join(home, ".codeclaw")
    """)


def _tmpl_dockerfile() -> str:
    return textwrap.dedent("""\
    # CodeClaw Dockerfile — Multi-stage, imagen mínima
    FROM python:3.12-slim AS builder
    WORKDIR /build
    COPY pyproject.toml .
    RUN pip install --no-cache-dir build && python -m build --wheel

    FROM python:3.12-slim
    WORKDIR /app
    RUN apt-get update && apt-get install -y --no-install-recommends \\
        curl sqlite3 && rm -rf /var/lib/apt/lists/*

    COPY --from=builder /build/dist/*.whl /tmp/
    RUN pip install --no-cache-dir /tmp/*.whl

    COPY . .

    ENV OPENCLAW_DATA_DIR=/data
    ENV OPENCLAW_ROLE=all
    ENV OPENCLAW_MODE=single

    VOLUME ["/data"]
    EXPOSE 8080

    HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \\
        CMD python -c "from codeclaw.api.health import health_check; h=health_check(); exit(0 if h['healthy'] else 1)"

    CMD ["python", "-m", "codeclaw.main"]
    """)


def _tmpl_docker_compose() -> str:
    return textwrap.dedent("""\
    version: "3.9"

    x-common: &common
      image: codeclaw:latest
      restart: unless-stopped
      volumes:
        - codeclaw_data:/data
      env_file: .env

    services:
      orchestrator:
        <<: *common
        environment:
          OPENCLAW_ROLE: orchestrator
        ports:
          - "8080:8080"

      curator:
        <<: *common
        environment:
          OPENCLAW_ROLE: curator

      batch:
        <<: *common
        environment:
          OPENCLAW_ROLE: batch
          OLLAMA_HOST: http://ollama:11434
        depends_on:
          - ollama

      ollama:
        image: ollama/ollama
        volumes:
          - ollama_models:/root/.ollama
        ports:
          - "11434:11434"

    volumes:
      codeclaw_data:
      ollama_models:
    """)


def _tmpl_readme() -> str:
    return textwrap.dedent("""\
    # 🦀 CodeClaw

    > Hybrid Autonomous Agent Infrastructure

    **80% determinista · 15% estructurado · 5% LLM**

    ## Inicio Rápido

    ```bash
    git clone https://github.com/tuusuario/codeclaw
    cd codeclaw
    cp .env.example .env
    pip install -e ".[all]"
    python -m codeclaw.main
    ```

    ## Documentación

    - [Arquitectura de Memoria](docs/memory-architecture.md)
    - [Integración LLM](docs/llm-providers.md)
    - [Tool Orchestration](docs/tool-orchestration.md)
    - [Self-Automation Engine](docs/self-automation.md)

    ## Tests

    ```bash
    pytest tests/ --tb=short -q
    ```

    ## Docker

    ```bash
    docker compose up orchestrator
    ```

    ---
    *CodeClaw v2.0.0 — Construido para durar, diseñado para ahorrar.*
    """)


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

async def main_async():
    print("🦀 CodeClaw Builder MCP Server iniciado", file=sys.stderr)
    print("   Esperando conexión de OpenCode...", file=sys.stderr)
    
    from mcp.server import InitializationOptions
    
    # Crear NotificationOptions vacío
    NotificationOptions = type('NotificationOptions', (), {
        'tools_changed': False, 
        'resources_changed': False, 
        'prompts_changed': False
    })
    notification_options = NotificationOptions()
    
    capabilities = server.get_capabilities(
        notification_options=notification_options,
        experimental_capabilities={}
    )
    
    options = InitializationOptions(
        server_name="codeclaw_builder",
        server_version="2.0.0",
        capabilities=capabilities,
        instructions=None
    )
    
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream=read_stream,
            write_stream=write_stream,
            initialization_options=options
        )


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()