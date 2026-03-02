"""
AI Bridge - Detecta y usa la IA disponible
Orden de prioridad: Ollama > Claude API > OpenCode > None
"""

import sys
import logging
import json
import subprocess
import os
from pathlib import Path
from typing import Optional, Dict

CEREBRO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CEREBRO_ROOT))

from config.config_loader import load_config, load_nodes

logger = logging.getLogger("cerebro")


class AIBridge:
    """Puente hacia sistemas de IA disponibles"""

    def __init__(self):
        self.config = load_config()
        self.client = self._detect_available_ai()

    def _detect_available_ai(self):
        """Detecta qué IA está disponible"""
        # 1. Ollama local
        if self.config.get("prefer_local", True):
            try:
                from ai.ollama_client import OllamaClient

                client = OllamaClient(
                    self.config.get("ollama_url", "http://localhost:11434")
                )
                if client.is_available():
                    logger.info("IA detectada: Ollama (local)")
                    return client
            except:
                pass

        # 2. Claude API
        if self.config.get("claude_api_key"):
            try:
                from ai.claude_client import ClaudeClient

                client = ClaudeClient(self.config.get("claude_api_key"))
                if client.is_available():
                    logger.info("IA detectada: Claude API")
                    return client
            except:
                pass

        # 3. OpenCode
        if self._check_opencode():
            try:
                from ai.opencode_client import OpenCodeClient

                client = OpenCodeClient()
                logger.info("IA detectada: OpenCode")
                return client
            except:
                pass

        logger.warning("No se detectó ninguna IA - usando solo reglas predefinidas")
        return None

    def _check_opencode(self) -> bool:
        """Verifica si opencode está instalado"""
        result = subprocess.run(["which", "opencode"], capture_output=True, text=True)
        return result.returncode == 0

    def is_available(self) -> bool:
        """Verifica si hay alguna IA disponible"""
        return self.client is not None

    def ask(self, prompt: str, context: str = None) -> str:
        """
        Envía pregunta a la IA disponible
        """
        if not self.client:
            return "No hay IA disponible. Usa las reglas predefinidas."

        try:
            return self.client.ask(prompt, context)
        except Exception as e:
            logger.error(f"Error al preguntar a la IA: {e}")
            return f"Error: {e}"

    def get_infrastructure_context(self) -> str:
        """
        Obtiene contexto actual de la infraestructura
        """
        context_parts = []

        # Estado de nodos
        nodes = load_nodes()
        context_parts.append(f"## Nodos configurados ({len(nodes)}):")

        status_dir = CEREBRO_ROOT / "status"

        for node in nodes:
            status_file = status_dir / f"{node['name']}_latest.json"

            if status_file.exists():
                with open(status_file) as f:
                    status = json.load(f)

                metrics = status.get("metrics", {})
                context_parts.append(
                    f"- {node['name']}: "
                    f"CPU={metrics.get('cpu_percent', 'N/A')}%, "
                    f"RAM={metrics.get('ram_percent', 'N/A')}%, "
                    f"Disco={metrics.get('disk_percent', 'N/A')}%"
                )
            else:
                context_parts.append(f"- {node['name']}: Sin datos")

        # Problemas recientes
        log_file = CEREBRO_ROOT / "logs" / "cerebro.log"
        if log_file.exists():
            with open(log_file) as f:
                lines = f.readlines()

            warnings = [l for l in lines[-50:] if "WARNING" in l or "CRITICAL" in l]
            if warnings:
                context_parts.append("\n## Últimos warnings:")
                context_parts.extend([f"- {w.strip()}" for w in warnings[-5:]])

        return "\n".join(context_parts)

    def extract_commands(self, response: str) -> list:
        """
        Extrae comandos bash de la respuesta de la IA
        """
        import re

        # Buscar bloques de código
        code_blocks = re.findall(r"```bash\n(.*?)```", response, re.DOTALL)

        # También buscar líneas que empiecen con $
        dollar_commands = re.findall(r"^\$\s+(.+)$", response, re.MULTILINE)

        commands = []
        commands.extend([cmd.strip() for cmd in code_blocks])
        commands.extend([cmd.strip() for cmd in dollar_commands])

        return commands
