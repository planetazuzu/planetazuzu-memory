"""
Telepathy - Sistema de alertas multicanal
Notificaciones por Telegram, Email y logs
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

CEREBRO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CEREBRO_ROOT))

logger = logging.getLogger("cerebro")


class Telepathy:
    """Sistema de notificaciones y alertas"""

    def __init__(self):
        self.config = self._load_telegram_config()
        self.last_alerts = {}
        self.cooldown_minutes = 30

    def _load_telegram_config(self) -> dict:
        """Carga configuración de Telegram"""
        config_file = CEREBRO_ROOT / "config" / "telegram.conf"

        defaults = {"enabled": False, "bot_token": "", "chat_id": ""}

        if not config_file.exists():
            return defaults

        config = {}
        with open(config_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()

        return {**defaults, **config}

    def send_alert(self, message: str, level: str = "INFO", node: str = None):
        """
        Envía alerta por múltiples canales
        - Telegram (si configurado)
        - Email (si configurado)
        - Siempre escribe en log
        """
        # Verificar cooldown para evitar spam
        alert_key = f"{message[:50]}"
        if self._should_skip(alert_key):
            logger.debug(f"Alerta ignorada (cooldown): {message[:50]}")
            return

        # Formatear mensaje
        formatted = self._format_message(message, level, node)

        # Log siempre
        if level == "CRITICAL":
            logger.critical(formatted)
        elif level == "WARNING":
            logger.warning(formatted)
        else:
            logger.info(formatted)

        # Intentar Telegram
        if self.config.get("enabled"):
            self._send_telegram(formatted)

        # Intentar Email
        self._send_email(formatted, level)

    def _should_skip(self, alert_key: str) -> bool:
        """Verifica si la alerta debe saltarse por cooldown"""
        now = datetime.now()

        if alert_key in self.last_alerts:
            last_time = self.last_alerts[alert_key]
            if now - last_time < timedelta(minutes=self.cooldown_minutes):
                return True

        self.last_alerts[alert_key] = now
        return False

    def _format_message(self, message: str, level: str, node: Optional[str]) -> str:
        """Formatea el mensaje de alerta"""
        node_str = f"[NODO:{node}]" if node else ""
        return f"[CEREBRO]{node_str}[{level}] {message}"

    def _send_telegram(self, message: str) -> bool:
        """Envía mensaje por Telegram"""
        if not self.config.get("bot_token") or not self.config.get("chat_id"):
            return False

        try:
            import requests

            url = f"https://api.telegram.org/bot{self.config['bot_token']}/sendMessage"
            data = {
                "chat_id": self.config["chat_id"],
                "text": message,
                "parse_mode": "Markdown",
            }

            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error enviando Telegram: {e}")
            return False

    def _send_email(self, message: str, level: str):
        """Envía email (stub - implementar con smtplib si se necesita)"""
        # Por ahora solo log
        # Implementar con configuración de email en email.conf
        pass

    def send_daily_report(self, report: dict):
        """Envía reporte diario"""
        message = f"Reporte Diario CEREBRO\n"
        message += f"Acciones: {len(report.get('actions', []))}\n"
        message += f"Warnings: {len(report.get('warnings', []))}"

        self.send_alert(message, "INFO")

    def send_weekly_report(self, report: dict):
        """Envía reporte semanal"""
        message = f"Reporte Semanal CEREBRO\n"
        message += f"Acciones: {len(report.get('actions', []))}\n"
        message += f"Warnings: {len(report.get('warnings', []))}"

        self.send_alert(message, "INFO")
