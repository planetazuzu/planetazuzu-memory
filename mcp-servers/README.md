# MCP Servers

Colección de MCP servers instalados en el servidor Nexus.

## Servidores Incluidos

### 1. linkedin_mcp
- **Lenguaje:** Python
- **Descripción:** MCP Server para gestión de LinkedIn usando Playwright con comportamiento humano simulado
- **Ubicación:** `/root/linkedin_mcp/`
- **Características:**
  - Automatización de LinkedIn
  - Envío de mensajes
  - Integración con Telegram para notificaciones
  - Google Sheets integration

### 2. mcp-finanzas
- **Lenguaje:** Python
- **Descripción:** Servidor HTTP independiente para gestión de finanzas
- **Ubicación:** `/root/mcp-finanzas/`
- **Características:**
  - Herramientas financieras via HTTP API
  - FastAPI para exponer herramientas
  - Integración con finbot

### 3. server-monitor
- **Lenguaje:** Node.js
- **Descripción:** Daemon de monitoreo de servidor con alertas
- **Ubicación:** `/opt/server-monitor/`
- **Características:**
  - Métricas: CPU, Memoria, Disco, Swap
  - Monitoreo de procesos (detección de zombies)
  - Monitoreo de PostgreSQL
  - Monitoreo de Docker
  - Notificaciones Telegram y Email
  - Limpieza automática
  - Reportes diarios

## Estado en el Servidor

| MCP | Estado | Notas |
|-----|--------|-------|
| linkedin_mcp | ⚠️ | Requiere credenciales LinkedIn |
| mcp-finanzas | ⚠️ | Requiere configuración finbot |
| server-monitor | ✅ | Funcional como MCP para OpenCode |

## Uso

### server-monitor (recomendado)
```bash
cd /opt/server-monitor
npm install
cp .env.example .env
# Configurar variables de entorno
./install.sh
```

### linkedin_mcp
```bash
cd /root/linkedin_mcp
pip install -r requirements.txt
python server.py
```

### mcp-finanzas
```bash
cd /root/mcp-finanzas
pip install -r requirements.txt
python server.py
```
