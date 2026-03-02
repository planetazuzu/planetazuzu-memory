"""
Scheduler - Tareas programadas de mantenimiento
Daily y weekly maintenance
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

CEREBRO_ROOT = Path(__file__).parent.parent
import sys

sys.path.insert(0, str(CEREBRO_ROOT))

from config.config_loader import load_nodes
from core.monitor import Monitor

logger = logging.getLogger("cerebro")


class Scheduler:
    """Programador de tareas de mantenimiento"""

    def __init__(self):
        self.monitor = Monitor()
        self.status_dir = CEREBRO_ROOT / "status"
        self.status_dir.mkdir(parents=True, exist_ok=True)

    def daily_maintenance(self):
        """
        Mantenimiento diario - se ejecuta a las 3am
        """
        logger.info("Iniciando daily_maintenance...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "type": "daily",
            "actions": [],
            "warnings": [],
        }

        nodes = load_nodes()

        for node in nodes:
            logger.info(f"Daily maintenance en {node['name']}...")

            # Actualizar seguridad solo
            result = self.monitor.execute_command(
                node, "apt-get update && apt-get upgrade --only-upgrade -y"
            )

            if result.get("success"):
                report["actions"].append(f"Actualizado {node['name']}")
            else:
                report["warnings"].append(f"Error actualizando {node['name']}")

            # Rotar logs
            self.monitor.execute_command(
                node, "find /var/log -name '*.log' -mtime +7 -compress"
            )

            # Limpiar /tmp
            self.monitor.execute_command(
                node, "find /tmp -type f -atime +3 -delete 2>/dev/null"
            )

            # Verificar backups
            backup_check = self.monitor.execute_command(
                node, "ls -lt /backup 2>/dev/null | head -1"
            )

            if backup_check.get("output"):
                # Parsear fecha del archivo más reciente
                output = backup_check["output"]
                if "cannot access" in output.lower():
                    report["warnings"].append(f"No hay backups en {node['name']}")
            else:
                report["warnings"].append(f"Backup check falló en {node['name']}")

        # Guardar reporte
        date_str = datetime.now().strftime("%Y%m%d")
        report_file = self.status_dir / f"daily_{date_str}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Daily maintenance completado: {len(report['actions'])} acciones")

        return report

    def weekly_maintenance(self):
        """
        Mantenimiento semanal - se ejecuta cada domingo a las 4am
        """
        logger.info("Iniciando weekly_maintenance...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "type": "weekly",
            "actions": [],
            "warnings": [],
            "security_audit": {},
        }

        nodes = load_nodes()

        for node in nodes:
            logger.info(f"Weekly maintenance en {node['name']}...")

            # Upgrade completo
            result = self.monitor.execute_command(
                node, "apt-get update && apt-get upgrade -y"
            )

            if result.get("success"):
                report["actions"].append(f"Upgrade completo en {node['name']}")

            # Auditar usuarios
            users_check = self.monitor.execute_command(
                node, "awk -F: '($3 == 0) {print}' /etc/passwd"
            )

            root_users = users_check.get("output", "").strip()
            if root_users:
                report["security_audit"]["root_users"] = root_users.split("\n")

            # Verificar puertos abiertos
            ports_check = self.monitor.execute_command(
                node, "ss -tlnp | grep -v 'State'"
            )

            open_ports = ports_check.get("output", "")
            port_count = len([l for l in open_ports.split("\n") if l.strip()])
            report["security_audit"][node["name"]] = {
                "open_ports": port_count,
                "details": open_ports[:500],
            }

            # Verificar SSH
            ssh_check = self.monitor.execute_command(
                node,
                "grep -v '^#' /etc/ssh/sshd_config | grep -E '^(PermitRootLogin|PasswordAuthentication)'",
            )

            if ssh_check.get("output"):
                report["security_audit"][f"{node['name']}_ssh"] = ssh_check["output"]

        # Guardar reporte semanal
        date_str = datetime.now().strftime("%Y%m%d")
        report_file = self.status_dir / f"weekly_{date_str}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Weekly maintenance completado")

        return report
