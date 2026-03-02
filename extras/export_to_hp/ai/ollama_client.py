"""
Ollama Client - Cliente para Ollama local
"""

import requests
import json
import logging
from typing import Optional

logger = logging.getLogger("cerebro")


class OllamaClient:
    """Cliente para Ollama local"""

    SYSTEM_PROMPT = """Eres un ingeniero DevOps experto. Analizas problemas de infraestructura 
y das soluciones concretas con comandos bash ejecutables. 
Siempre que sea posible, proporcionas los comandos exactos para resolver el problema.
Si no estás seguro de algo, lo indicas claramente."""

    def __init__(self, url: str = "http://localhost:11434"):
        self.url = url
        self.model = self._detect_model()

    def is_available(self) -> bool:
        """Verifica si Ollama está disponible"""
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _detect_model(self) -> str:
        """Detecta qué modelo está disponible"""
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                if models:
                    # Usar el primer modelo disponible
                    return models[0]["name"]
        except:
            pass

        return "llama2"  # Default

    def ask(self, prompt: str, context: str = None) -> str:
        """
        Envía pregunta a Ollama
        """
        full_prompt = f"{prompt}\n\n{context}" if context else prompt

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "system": self.SYSTEM_PROMPT,
            "stream": False,
        }

        try:
            response = requests.post(
                f"{self.url}/api/generate", json=payload, timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "Sin respuesta")
            else:
                return f"Error: {response.status_code}"

        except requests.exceptions.Timeout:
            return "Error: Timeout al conectar con Ollama"
        except Exception as e:
            return f"Error: {e}"

    def get_model_info(self) -> dict:
        """Obtiene información del modelo actual"""
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}
