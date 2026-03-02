---
name: free-models-only
description: "Fuerza el uso exclusivo de modelos gratuitos/sin coste. Aplicar SIEMPRE que se use cualquier modelo de IA."
---

# Free Models Only

**Regla obligatoria:** Solo usar modelos gratuitos. Si un modelo tiene coste, rechazar y usar alternativa.

## Modelos Gratuitos por Plataforma

### OpenClaw (BlackBox - este servidor)
| Modelo | Provider | Uso |
|--------|----------|-----|
| opencode/glm-5-free | GLM | Tareas generales |
| opencode/kimi-k2.5-free | Moonshot | Alternativo |
| opencode/claude-opus-4-6 | OpenCode | Default (verificar si free) |

### Ollama Local (localhost:11434)
| Modelo | Tamaño | Uso |
|--------|--------|-----|
| llama3.2:8b | 8B | General, rápido |
| qwen3:8b | 8B | Alternativo |
| deepseek-coder:6.7b | 6.7B | Código |
| nomic-embed-text | - | Embeddings |

### ClawDev (G1)
| Modelo | Uso |
|--------|-----|
| ollama/qwen3:8b | Local en G1 |
| opencode/glm-5-free | Cloud gratis |

## Fallback Chain (usar en orden)

1. **Ollama local** (llama3.2:8b) — 0€, sin rate limit
2. **opencode/glm-5-free** — Gratis, rate limit
3. **opencode/kimi-k2.5-free** — Backup gratis

## Comandos

### OpenCode en BlackBox
```bash
/root/.opencode/bin/opencode run "tarea" --model ollama/llama3.2:8b
/root/.opencode/bin/opencode run "tarea" --model opencode/glm-5-free
```

### OpenCode en ClawDev
```bash
ssh clawdev "~/.opencode/bin/opencode run 'tarea' --model ollama/qwen3:8b"
```

## Detección de Rate Limit

Si un modelo gratis devuelve rate limit (HTTP 429), auto-switch:
- glm-5-free → kimi-k2.5-free → ollama/llama3.2:8b

## Prohibido

- NO usar modelos con coste (Claude, GPT-4, etc.) sin autorización explícita
- NO usar default model si tiene coste
- Siempre especificar `--model` explícitamente

## Aplicación

Esta skill aplica a:
- BlackBox (este servidor)
- ClawDev (G1) vía SSH
- Cualquier subagente spawnado
