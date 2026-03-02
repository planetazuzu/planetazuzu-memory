# Extras - Proyectos Adicionales

## Contenido

### alert_hub/
Bot de alertas que notifica por Telegram:
- Gmail: Emails importantes con enlaces directos
- LinkedIn: Notificaciones
- WhatsApp: Futuro

**Archivos:**
- `server.py` - Servidor principal
- `requirements.txt` - Dependencias
- `.env` - Configuración
- `deploy.sh` - Script de despliegue
- `cron_check.sh` - Verificación de cron

**Uso:**
```bash
cd alert_hub
pip install -r requirements.txt
python server.py
```

---

### export_to_hp/
Sistema de IA modular con cerebro y MCPs.

**Estructura:**
```
export_to_hp/
├── ai/                    # Clientes IA
│   ├── bridge.py         # Puente entre clientes
│   ├── claude_client.py  # Cliente Claude
│   ├── ollama_client.py  # Cliente Ollama
│   └── opencode_client.py
│
├── core/                 # Nucleo del sistema
│   ├── daemon.py        # Demonio principal
│   ├── healer.py        # Auto-curación
│   ├── monitor.py       # Monitor del sistema
│   ├── scheduler.py    # Programador
│   └── telepathy.py    # Comunicación
│
└── mcp/                 # MCPs integrados
    ├── alert/          # Alertas
    ├── finanzas/       # Finanzas
    ├── gmail/          # Gmail
    └── linkedin/       # LinkedIn
```

---

### mcp/codeclaw_builder_mcp.py
MCP Server para OpenCode que construye el proyecto CodeClaw.

**Características:**
- Construye CodeClaw completo
- Valida cada fase
- No abandona hasta completar

**Uso:**
```bash
# En OpenCode
opencode --mcp codeclaw_builder

# O en config.json
{
  "mcpServers": {
    "codeclaw": {
      "command": "python",
      "args": ["codeclaw_builder_mcp.py"]
    }
  }
}
```

---
*Última actualización: 2026-03-02*
