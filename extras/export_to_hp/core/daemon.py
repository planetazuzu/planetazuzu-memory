"""
Daemon principal de CEREBRO - Proceso independiente de monitorización
"""

import os
import sys
import time
import signal
import logging
import logging.handlers
import json
import fcntl
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread, Event

CEREBRO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CEREBRO_ROOT))

from core.monitor import Monitor
from core.healer import Healer
from core.scheduler import Scheduler
from core.telepathy import Telepathy
from config.config_loader import load_nodes, load_config


class CerebroDaemon:
    """Daemon principal de CEREBRO que corre como proceso independiente"""

    _instance = None
    _stop_event = Event()
    _daemon_thread = None
    _pid_file = Path("/var/run/cerebro.pid")

    @classmethod
    def start_daemon(cls):
        """Inicia el daemon de CEREBRO"""
        # Verificar si ya hay una instancia corriendo
        if cls._pid_file.exists():
            with open(cls._pid_file) as f:
                old_pid = int(f.read().strip())
            try:
                os.kill(old_pid, 0)
                print(f"Ya hay una instancia corriendo con PID {old_pid}")
                return False
            except OSError:
                cls._pid_file.unlink()

        # Escribir PID
        with open(cls._pid_file, "w") as f:
            f.write(str(os.getpid()))

        # Configurar logging
        cls._setup_logging()

        # Iniciar thread del daemon
        cls._stop_event.clear()
        cls._daemon_thread = Thread(target=cls._daemon_loop, daemon=True)
        cls._daemon_thread.start()

        cls.logger.info(f"CEREBRO daemon iniciado con PID {os.getpid()}")
        return True

    @classmethod
    def stop_daemon(cls):
        """Detiene el daemon de CEREBRO"""
        cls._stop_event.set()
        if cls._daemon_thread:
            cls._daemon_thread.join(timeout=10)

        if cls._pid_file.exists():
            cls._pid_file.unlink()

        cls.logger.info("CEREBRO daemon detenido")

    @classmethod
    def _setup_logging(cls):
        """Configura el sistema de logging con rotación"""
        log_file = CEREBRO_ROOT / "logs" / "cerebro.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        cls.logger = logging.getLogger("cerebro")
        cls.logger.setLevel(logging.DEBUG)

        # Handler con rotación
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        cls.logger.addHandler(handler)

        # También logger a stdout
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        cls.logger.addHandler(console)

    @classmethod
    def _daemon_loop(cls):
        """Bucle principal del daemon"""
        cls.logger.info("Iniciando bucle principal de CEREBRO")

        # Tiempos de las últimas ejecuciones
        last_full_check = datetime.min
        last_security_check = datetime.min
        last_daily_maintenance = datetime.min
        last_weekly_maintenance = datetime.min

        monitor = Monitor()
        healer = Healer()
        scheduler = Scheduler()

        while not cls._stop_event.is_set():
            now = datetime.now()

            try:
                # Cada 5 minutos: check_all_nodes
                cls.logger.debug("Ejecutando check_all_nodes...")
                nodes = load_nodes()
                for node in nodes:
                    try:
                        monitor.check_node(node)
                    except Exception as e:
                        cls.logger.error(f"Error al verificar nodo {node['name']}: {e}")

                # Verificar si hay problemas que necesitan heal
                healer.process_checks()

                # Cada 1 hora: check_services + check_security
                if now - last_full_check >= timedelta(hours=1):
                    cls.logger.info("Ejecutando check_services y check_security...")
                    for node in nodes:
                        try:
                            monitor.check_services(node)
                            monitor.check_security(node)
                        except Exception as e:
                            cls.logger.error(f"Error en checks de {node['name']}: {e}")
                    last_full_check = now

                # Cada domingo a las 4am: weekly_maintenance
                if (
                    now.weekday() == 6
                    and now.hour >= 4
                    and now - last_weekly_maintenance >= timedelta(days=7)
                ):
                    cls.logger.info("Ejecutando weekly_maintenance...")
                    scheduler.weekly_maintenance()
                    last_weekly_maintenance = now

                # Cada día a las 3am: daily_maintenance
                if now.hour >= 3 and now - last_daily_maintenance >= timedelta(days=1):
                    cls.logger.info("Ejecutando daily_maintenance...")
                    scheduler.daily_maintenance()
                    last_daily_maintenance = now

            except Exception as e:
                cls.logger.error(f"Error en el bucle principal: {e}")

            # Dormir 5 minutos
            cls._stop_event.wait(300)

        cls.logger.info("Bucle principal terminado")


def signal_handler(signum, frame):
    """Maneja señales del sistema"""
    logger = logging.getLogger("cerebro")
    logger.info(f"Recibida señal {signum}, deteniendo...")
    CerebroDaemon.stop_daemon()
    sys.exit(0)


def run_daemon():
    """Función principal para correr como daemon"""
    # Configurar manejadores de señales
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Importar aquí para evitar circular imports
    import logging.handlers

    CerebroDaemon.start_daemon()

    # Mantener el proceso vivo
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        CerebroDaemon.stop_daemon()


if __name__ == "__main__":
    run_daemon()
