"""
Claude Client - Cliente para Anthropic Claude API
"""

import requests
import json
import logging
from typing import Optional

logger = logging.getLogger("cerebro")


class ClaudeClient:
    """Cliente para Anthropic Claude API"""

    SYSTEM_PROMPT = """Eres un ingeniero DevOps experto. Analizas problemas de infraestructura 
y das soluciones concretas con comandos bash ejecutables. 
Siempre que sea posible, proporcionas los comandos exactos para resolver el problema.
Si no estás seguro de algo, lo indicas claramente."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-20251114"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"

    def is_available(self) -> bool:
        """Verifica si la API está disponible"""
        if not self.api_key:
            return False

        # Verificar que podemos hacer una petición simple
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            # Usar claude-3-haiku que es más rápido y barato para verificación
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}],
            }

            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=10
            )

            return response.status_code in (200, 400)  # 400 ok si es el test

        except:
            return False

    def ask(self, prompt: str, context: str = None) -> str:
        """
        Envía pregunta a Claude
        """
        if not self.api_key:
            return "Error: No hay API key configurada"

        full_prompt = f"{prompt}\n\n{context}" if context else prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "system": self.SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": full_prompt}],
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("content", [{}])[0].get("text", "Sin respuesta")
            elif response.status_code == 429:
                return "Error: Rate limit excedido. Intenta más tarde."
            else:
                return f"Error: {response.status_code} - {response.text}"

        except requests.exceptions.Timeout:
            return "Error: Timeout al conectar con Claude API"
        except Exception as e:
            return f"Error: {e}"
