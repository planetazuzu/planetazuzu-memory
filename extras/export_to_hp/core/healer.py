"""
Healer - Sistema de auto-reparación basado en reglas
Ejecuta acciones correctivas cuando detecta problemas
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

CEREBRO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CEREBRO_ROOT))

from config.config_loader import load_nodes, load_rules, load_config
from core.monitor import Monitor
from core.telepathy import Telepathy
from ai.bridge import AIBridge

logger = logging.getLogger("cerebro")


class Healer:
    """Sistema de auto-reparación"""

    def __init__(self):
        self.rules = load_rules()
        self.config = load_config()
        self.monitor = Monitor()
        self.telepathy = Telepathy()
        self.ai_bridge = AIBridge()
        self.actions_log = []

    def process_checks(self):
        """
        Procesa los últimos resultados de checks y ejecuta acciones si es necesario
        """
        nodes = load_nodes()

        for node in nodes:
            status_file = CEREBRO_ROOT / "status" / f"{node['name']}_latest.json"
            if not status_file.exists():
                continue

            with open(status_file) as f:
                status = json.load(f)

            # Verificar servicios
            self._check_services(node)

            # Verificar métricas
            self._check_metrics(node, status)

            # Verificar seguridad
            self._check_security(node)

    def _check_services(self, node: Dict):
        """Verifica y repara servicios caídos"""
        services_file = CEREBRO_ROOT / "status" / f"{node['name']}_services.json"
        if not services_file.exists():
            return

        with open(services_file) as f:
            services_data = json.load(f)

        for service, info in services_data.get("services", {}).items():
            if not info.get("running", False):
                logger.warning(
                    f"{node['name']}: {service} está caído, intentando reparar..."
                )
                self._restart_service(node, service)

    def _check_metrics(self, node: Dict, status: Dict):
        """Verifica métricas y ejecuta acciones correctivas"""
        metrics = status.get("metrics", {})

        # Disco > 85%
        disk = metrics.get("disk_percent", 0)
        if disk > 85:
            logger.warning(f"{node['name']}: Disco al {disk}%")
            self._clean_disk(node)

        # RAM > 90%
        ram = metrics.get("ram_percent", 0)
        if ram > 90:
            logger.warning(f"{node['name']}: RAM al {ram}%")
            self._free_memory(node)

    def _check_security(self, node: Dict):
        """Procesa alertas de seguridad"""
        security_file = CEREBRO_ROOT / "status" / f"{node['name']}_security.json"
        if not security_file.exists():
            return

        with open(security_file) as f:
            security = json.load(f)

        if security.get("attack_ips"):
            for ip_info in security["attack_ips"]:
                self._block_ip(node, ip_info["ip"])

    def heal_node(self, node: Dict) -> Dict:
        """
        Fuerza revisión y reparación completa de un nodo
        """
        result = {"success": True, "message": "", "actions": []}

        logger.info(f"Iniciando heal completo para {node['name']}...")

        # Ejecutar todos los checks
        self.monitor.check_node(node)
        self.monitor.check_services(node)
        self.monitor.check_security(node)

        # Procesar resultados
        self._check_services(node)

        status_file = CEREBRO_ROOT / "status" / f"{node['name']}_latest.json"
        if status_file.exists():
            with open(status_file) as f:
                status = json.load(f)
            self._check_metrics(node, status)

        # Si hay problemas persistentes, escalar a IA
        if self._has_persistent_issues(node):
            logger.warning(f"{node['name']}: Problemas persistentes, escalando a IA...")
            self._escalate_to_ai(node)

        result["message"] = "Heal completado"
        return result

    def _restart_service(self, node: Dict, service: str, attempt: int = 1):
        """Intenta reiniciar un servicio"""
        if attempt > 3:
            self.telepathy.send_alert(
                f"Servicio {service} no se puede reiniciar en {node['name']}",
                "CRITICAL",
            )
            self._escalate_to_ai(
                node, f"Servicio {service} caído después de 3 intentos"
            )
            return

        logger.info(f"{node['name']}: Reiniciando {service} (intento {attempt}/3)")

        result = self.monitor.execute_command(
            node, f"systemctl restart {service} && systemctl is-active {service}"
        )

        if result.get("success") and "active" in result.get("output", ""):
            logger.info(f"{node['name']}: {service} reiniciado exitosamente")
            self.telepathy.send_alert(
                f"Servicio {service} reiniciado en {node['name']}", "INFO"
            )
        else:
            # Reintentar en 10 segundos
            import time

            time.sleep(10)
            self._restart_service(node, service, attempt + 1)

    def _clean_disk(self, node: Dict):
        """Limpia disco: /tmp, logs viejos"""
        logger.info(f"{node['name']}: Limpiando disco...")

        commands = [
            "rm -rf /tmp/* 2>/dev/null",
            "find /var/log -name '*.gz' -mtime +30 -delete 2>/dev/null",
            "find /var/log -name '*.log' -mtime +7 -size +100M -truncate 2>/dev/null",
        ]

        for cmd in commands:
            self.monitor.execute_command(node, cmd)

        self.telepathy.send_alert(
            f"Limpieza de disco ejecutada en {node['name']}", "INFO"
        )

    def _free_memory(self, node: Dict):
        """Libera memoria: reinicia proceso más costoso si es seguro"""
        logger.info(f"{node['name']}: Analizando memoria...")

        # Obtener proceso con más memoria
        result = self.monitor.execute_command(
            node,
            "ps aux --sort=-%mem | head -6 | tail -5 | awk '{print $11}' | head -1",
        )

        process = result.get("output", "").strip()

        # Procesos seguros para reiniciar
        safe_processes = ["nginx", "apache2", "php-fpm", "node", "python"]

        can_restart = any(safe in process for safe in safe_processes)

        if can_restart:
            # Reiniciar el proceso
            self.monitor.execute_command(
                node, f"systemctl restart {process.split()[0]}"
            )
            self.telepathy.send_alert(
                f"Proceso {process} reiniciado en {node['name']}", "WARNING"
            )

    def _block_ip(self, node: Dict, ip: str):
        """Bloquea IP atacante con fail2ban"""
        logger.info(f"{node['name']}: Bloqueando IP {ip}...")

        # Verificar si fail2ban está instalado
        result = self.monitor.execute_command(node, "which fail2ban-client")

        if result.get("success") and result.get("output"):
            self.monitor.execute_command(node, f"fail2ban-client set ssh banip {ip}")
            self.telepathy.send_alert(
                f"IP {ip} bloqueada en {node['name']} por fail2ban", "CRITICAL"
            )
        else:
            # Añadir a iptables manualmente
            self.monitor.execute_command(node, f"iptables -I INPUT -s {ip} -j DROP")
            self.telepathy.send_alert(
                f"IP {ip} bloqueada manualmente en {node['name']}", "CRITICAL"
            )

    def _renew_ssl_cert(self, node: Dict, domain: str):
        """Intenta renovar certificado SSL con certbot"""
        logger.info(f"{node['name']}: Intentando renovar cert para {domain}...")

        result = self.monitor.execute_command(
            node, f"certbot renew --cert-name {domain} --dry-run"
        )

        if result.get("success"):
            self.monitor.execute_command(node, f"certbot renew --cert-name {domain}")
            self.telepathy.send_alert(f"Certificado renovado para {domain}", "INFO")
        else:
            self.telepathy.send_alert(
                f"No se pudo renovar cert para {domain}", "WARNING"
            )
            self._escalate_to_ai(
                node, f"Certificado SSL de {domain} próximos a expirar"
            )

    def _has_persistent_issues(self, node: Dict) -> bool:
        """Determina si el nodo tiene problemas persistentes"""
        # Leer estado reciente
        status_file = CEREBRO_ROOT / "status" / f"{node['name']}_latest.json"

        if not status_file.exists():
            return False

        # Por ahora, return False - se puede mejorar con historial
        return False

    def _escalate_to_ai(self, node: Dict, problem: str = ""):
        """Escala problema a la IA para análisis"""
        if not self.config.get("escalate_after_minutes"):
            return

        context = self.ai_bridge.get_infrastructure_context()

        prompt = f"""
Nodo {node["name"]} tiene problemas persistentes.
{problem}

Métricas actuales:
{context}

Analiza y sugiere acciones de reparación.
"""

        response = self.ai_bridge.ask(prompt)

        self.telepathy.send_alert(
            f"IA analizó {node['name']}: {response[:200]}...", "WARNING"
        )
