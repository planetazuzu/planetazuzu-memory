#!/bin/bash
# deploy_linkedin.sh - Instala los cronjobs de LinkedIn MCP

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

(crontab -l 2>/dev/null | grep -v "linkedin_mcp" || true) > /tmp/current_cron

cat >> /tmp/current_cron << 'EOF'
# LinkedIn MCP - Leer y clasificar mensajes (cada 30 min, 9:00-20:00)
*/30 9-19 * * * cd $SCRIPT_DIR && /usr/bin/python3 cronjobs/linkedin_alertas.py leer_clasificar >> /var/log/linkedin_mcp.log 2>&1

# LinkedIn MCP - Resumen diario (9:00)
0 9 * * * cd $SCRIPT_DIR && /usr/bin/python3 cronjobs/linkedin_alertas.py resumen >> /var/log/linkedin_mcp.log 2>&1
EOF

crontab /tmp/current_cron
echo "✅ Cronjobs de LinkedIn MCP instalados"
crontab -l | grep linkedin
