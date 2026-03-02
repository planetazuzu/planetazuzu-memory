#!/bin/bash
# deploy_gmail.sh - Instala los cronjobs de Gmail MCP

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Limpiar cronjobs anteriores de gmail_mcp
(crontab -l 2>/dev/null | grep -v "gmail_mcp" || true) > /tmp/current_cron

# Añadir las tareas al crontab
cat >> /tmp/current_cron << 'EOF'
# Gmail MCP - Monitorizar correos nuevos (cada 15 min)
*/15 * * * * cd $SCRIPT_DIR && /usr/bin/python3 cronjobs/gmail_alertas.py monitorizar >> /var/log/gmail_mcp.log 2>&1

# Gmail MCP - Resumen matutino (8:00 diario)
0 8 * * * cd $SCRIPT_DIR && /usr/bin/python3 cronjobs/gmail_alertas.py resumen >> /var/log/gmail_mcp.log 2>&1
EOF

crontab /tmp/current_cron
echo "✅ Cronjobs de Gmail MCP instalados"
crontab -l | grep gmail_mcp
