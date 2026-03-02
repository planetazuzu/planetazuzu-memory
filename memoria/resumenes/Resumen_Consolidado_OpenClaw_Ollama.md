# 📋 1. Consolidación de Configuración y Orquestación en OpenClaw con Ollama

## 🎯 2. Objetivo de la conversación

Configurar un entorno funcional y optimizado de OpenClaw en un portátil
Lenovo con 8 GB de RAM (con zram), integrando: - Ollama como motor local
de modelos. - Modelo qwen2.5-coder:7b para programación. - Modelo ligero
para sub-agents. - OpenCode y Google Antigravity para análisis y
orquestación. - Telegram como canal activo. - Evaluación e instalación
de skills desde ClawHub.

------------------------------------------------------------------------

## 📌 3. Puntos clave tratados

-   Instalación correcta de Ollama en Pop!\_OS.
-   Configuración optimizada para 8 GB RAM:
    -   OLLAMA_NUM_PARALLEL=1
    -   OLLAMA_MAX_LOADED_MODELS=1
-   Instalación de modelos:
    -   phi3 (ligero)
    -   qwen2.5-coder:7b (principal)
-   Confirmación de descarga exitosa del modelo coder.
-   Diferencias entre tipos de "skills" en ClawHub.
-   Imposibilidad de instalar ciertas skills como plugins ejecutables.
-   Integración conceptual de "Dynamic Model Selector".
-   Resolución de problemas de Telegram allowlist.
-   Uso correcto de OpenClaw TUI (`openclaw tui`).
-   Clarificación sobre comandos inexistentes (`openclaw chat`).
-   Comprensión de instancias tipo Backbox vs Forge.
-   Identificación de límites reales del sistema de instalación de
    skills.

------------------------------------------------------------------------

## 💡 4. Ideas principales y conclusiones

### Infraestructura actual

-   Sistema: Pop!\_OS
-   Hardware: 8 GB RAM + zram
-   Ollama en modo CPU-only
-   OpenClaw versión 2026.2.6
-   Gateway operativo
-   Telegram y WhatsApp conectados
-   Modelo principal: qwen2.5-coder:7b
-   Modelo ligero disponible: phi3

### Conclusiones técnicas

1.  Ollama quedó correctamente instalado y optimizado.
2.  qwen2.5-coder:7b funciona en CPU con límites adecuados.
3.  OpenClaw no usa `openclaw chat`; el modo correcto es `openclaw tui`.
4.  ClawHub mezcla dos tipos de skills:
    -   Plugins ejecutables (instalables)
    -   Skills conceptuales/documentales (no instalables)
5.  "Dynamic Model Selector" es una guía conceptual, no un plugin.
6.  Las skills externas solo pueden cargarse desde disco si contienen
    manifest válido.
7.  Telegram allowlist debe usar ID numérico o username humano, no bots.
8.  Backbox y Forge representan perfiles de ejecución (seguridad vs
    flexibilidad).

### Lecciones aprendidas

-   No todos los recursos en ClawHub son instalables.
-   Es necesario validar presencia de `skill.json` o `manifest.json`.
-   Las respuestas generadas por el agente pueden incluir comandos no
    soportados en la versión instalada.
-   Separar claramente orquestación (Antigravity) de ejecución (Ollama).

------------------------------------------------------------------------

## 📚 5. Recursos y ejemplos compartidos

### Modelos instalados

-   phi3:latest
-   qwen2.5-coder:7b

### Variables críticas aplicadas

    OLLAMA_NUM_PARALLEL=1
    OLLAMA_MAX_LOADED_MODELS=1

### Comandos clave utilizados

    ollama pull qwen2.5-coder:7b
    openclaw tui
    openclaw config apply
    openclaw gateway restart
    openclaw skills list

### Skill analizada

Dynamic Model Selector (ClawHub) - SKILL.md - scripts/classify_task.py -
references/models.md

------------------------------------------------------------------------

## ❓ 6. Preguntas pendientes o acciones sugeridas

1.  Integrar formalmente Ollama como provider en OpenClaw.
2.  Configurar agent `coder` con modelo qwen2.5-coder:7b.
3.  Definir modelo ligero para sub-agents.
4.  Implementar lógica automática de selección de modelo en prompt base.
5.  Probar flujo completo:
    -   Análisis (OpenCode)
    -   Decisión (Antigravity)
    -   Ejecución (Ollama)
6.  Evaluar si se requiere sandbox restrictivo (Backbox) o perfil
    flexible (Forge).

------------------------------------------------------------------------

## 📝 7. Notas adicionales

-   No hubo errores críticos de instalación.
-   La mayoría de bloqueos estuvieron relacionados con:
    -   Expectativas incorrectas sobre instalación automática de skills.
    -   Comandos obsoletos o no disponibles.
-   La infraestructura actual es estable y lista para integración
    completa con OpenClaw.
