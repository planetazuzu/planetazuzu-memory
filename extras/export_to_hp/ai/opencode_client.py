"""
OpenCode Client - Cliente para OpenCode CLI
"""

import subprocess
import logging
import os
from typing import Optional

logger = logging.getLogger("cerebro")


class OpenCodeClient:
    """Cliente para OpenCode CLI"""

    def __init__(self, path: str = None):
        self.path = path or "opencode"

    def is_available(self) -> bool:
        """Verifica si OpenCode está instalado"""
        try:
            result = subprocess.run(
                [self.path, "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def ask(self, prompt: str, context: str = None) -> str:
        """
        Ejecuta OpenCode con el prompt dado
        """
        full_prompt = f"{prompt}\n\n{context}" if context else prompt

        # Crear archivo temporal con el prompt
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(full_prompt)
            prompt_file = f.name

        try:
            # Ejecutar opencode con el archivo
            result = subprocess.run(
                [self.path, prompt_file],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutos
                cwd=os.getcwd(),
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"

        except subprocess.TimeoutExpired:
            return "Error: Timeout esperando respuesta de OpenCode"
        except Exception as e:
            return f"Error: {e}"
        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(prompt_file)
            except:
                pass
