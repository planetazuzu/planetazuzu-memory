"""
Configuración del MCP de Finanzas
"""
import os
from pathlib import Path

# Base de datos
BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "finanzas.db"

# Servidor
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "31434"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Límites
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB
REQUEST_TIMEOUT = 30  # segundos

# Categorías permitidas
ALLOWED_CATEGORIES = [
    "supermercado",
    "restaurantes",
    "ropa",
    "ocio",
    "belleza",
    "compras_online",
    "salud",
    "transporte",
    "deporte",
    "mascotas",
    "hogar",
    "viajes",
    "tabaco",
    "efectivo",
    "formacion",
    "sueldo",
    "inversion",
    "regalo",
    "otro"
]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
