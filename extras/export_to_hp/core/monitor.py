"""
Monitor - Módulo de monitorización de nodos y servicios
Recolecta métricas, verifica servicios y seguridad
"""

import os
import sys
import paramiko
import psutil
import socket
import ssl
import json
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional

CEREBRO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CEREBRO_ROOT))

from config.config_loader import load_nodes, load_domains

logger = logging.getLogger("cerebro")


class Monitor:
    """Monitor de nodos y servicios"""

    def __init__(self):
        self.nodes = load_nodes()
        self.results_dir = CEREBRO_ROOT / "status"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.previous_disk_data = self._load_previous_disk_data()

    def _load_previous_disk_data(self) -> Dict:
        """Carga datos de disco de ejecuciones anteriores"""
        disk_file = self.results_dir / "disk_history.json"
        if disk_file.exists():
            with open(disk_file) as f:
                return json.load(f)
        return {}

    def _save_disk_data(self, data: Dict):
        """Guarda datos de disco para comparaciones futuras"""
        disk_file = self.results_dir / "disk_history.json"
        with open(disk_file, "w") as f:
            json.dump(data, f)

    def check_node(self, node: Dict) -> Dict:
        """
        Verifica un nodo: ping + SSH + métricas
        """
        result = {
            "node": node["name"],
            "timestamp": datetime.now().isoformat(),
            "reachable": False,
            "ssh_ok": False,
            "metrics": {},
        }

        try:
            # Ping
            hostname = node["host"]
            response = socket.gethostbyname(hostname)
            result["reachable"] = True

            # Intentar SSH
            ssh_client = self._get_ssh_client(node)
            if ssh_client:
                result["ssh_ok"] = True
                result["metrics"] = self.get_metrics(ssh_client, node)
                ssh_client.close()

        except socket.gaierror:
            logger.warning(f"Node {node['name']}: No se pudo resolver {node['host']}")
        except Exception as e:
            logger.error(f"Node {node['name']}: Error al verificar - {e}")

        # Guardar resultado
        self._save_node_status(node["name"], result)
        return result

    def check_all_nodes(self) -> List[Dict]:
        """
        Verifica todos los nodos en paralelo
        """
        logger.info(f"Verificando {len(self.nodes)} nodos...")

        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.check_node, node): node for node in self.nodes
            }

            for future in as_completed(futures):
                node = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error verificando {node['name']}: {e}")

        return results

    def get_metrics(self, ssh_client, node: Dict) -> Dict:
        """
        Obtiene métricas del nodo vía SSH
        Detecta automáticamente arquitectura (x86_64 vs ARM)
        """
        metrics = {}

        try:
            # Detectar arquitectura
            stdin, stdout, stderr = ssh_client.exec_command("uname -m")
            arch = stdout.read().decode().strip()
            metrics["architecture"] = arch

            # Comandos para x86_64
            if arch in ["x86_64", "amd64"]:
                commands = {
                    "cpu_percent": "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1",
                    "ram_percent": "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'",
                    "disk_percent": "df -h / | tail -1 | awk '{print $5}' | cut -d'%' -f1",
                    "uptime": "uptime -p",
                    "load": "cat /proc/loadavg | awk '{print $1}'",
                }
            # Comandos para ARM (Raspberry Pi, etc)
            else:
                commands = {
                    "cpu_percent": "top -bn1 | head -3 | tail -1 | awk '{print $8}' | tr -d '%'",
                    "ram_percent": "free -m | awk 'NR==2{printf \"%.1f\", $3*100/$2}'",
                    "disk_percent": "df -h / | tail -1 | awk '{print $5}' | cut -d'%' -f1",
                    "uptime": "uptime -p",
                    "load": "cat /proc/loadavg | awk '{print $1}'",
                }

            for key, cmd in commands.items():
                stdin, stdout, stderr = ssh_client.exec_command(cmd)
                value = stdout.read().decode().strip()
                if value and value != "0" and value != "0.0":
                    try:
                        metrics[key] = float(value)
                    except ValueError:
                        metrics[key] = value

            # IP del nodo
            try:
                stdin, stdout, stderr = ssh_client.exec_command(
                    "hostname -I | awk '{print $1}'"
                )
                ip = stdout.read().decode().strip()
                if ip:
                    metrics["ip"] = ip
            except:
                pass

            # Temperatura (especialmente importante para RASPI)
            try:
                # Intentar varios métodos según el sistema
                temp_cmds = [
                    "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf \"%.1f\", $1/1000}'",
                    "vcgencmd measure_temp 2>/dev/null | cut -d= -f2 | cut -d'.' -f1",
                    "python3 -c \"import subprocess; print(subprocess.check_output(['vcgencmd', 'measure_temp']).decode().split('=')[1].split(\"'\\'')[0])\" 2>/dev/null",
                ]
                for cmd in temp_cmds:
                    stdin, stdout, stderr = ssh_client.exec_command(cmd)
                    temp = stdout.read().decode().strip()
                    if temp:
                        metrics["temperature"] = float(temp)
                        break
            except:
                pass

        except Exception as e:
            logger.error(f"Error obteniendo métricas de {node['name']}: {e}")

        return metrics

    def check_services(self, node: Dict) -> Dict:
        """
        Verifica servicios críticos listados en mutants.conf
        """
        result = {
            "node": node["name"],
            "timestamp": datetime.now().isoformat(),
            "services": {},
        }

        ssh_client = self._get_ssh_client(node)
        if not ssh_client:
            result["error"] = "No se pudo conectar SSH"
            return result

        try:
            services = node.get("services", [])

            for service in services:
                # Verificar si el servicio está corriendo
                stdin, stdout, stderr = ssh_client.exec_command(
                    f"systemctl is-active {service}"
                )
                status = stdout.read().decode().strip()

                result["services"][service] = {
                    "status": status,
                    "running": status == "active",
                }

                if status != "active":
                    logger.warning(
                        f"Node {node['name']}: Servicio {service} no está activo"
                    )

        except Exception as e:
            logger.error(f"Error verificando servicios en {node['name']}: {e}")
            result["error"] = str(e)
        finally:
            ssh_client.close()

        # Guardar resultado
        status_file = self.results_dir / f"{node['name']}_services.json"
        with open(status_file, "w") as f:
            json.dump(result, f, indent=2)

        return result

    def check_ssl(self, domains: List[Dict] = None) -> List[Dict]:
        """
        Verifica certificados SSL de dominios
        """
        if domains is None:
            domains = load_domains()

        results = []

        for domain_info in domains:
            try:
                hostname = domain_info["domain"]
                port = domain_info.get("port", 443)

                context = ssl.create_default_context()
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()

                        # Parsear fecha de expiración
                        not_after = datetime.strptime(
                            cert["notAfter"], "%b %d %H:%M:%S %Y %z"
                        )
                        days_left = (not_after - datetime.now()).days

                        result = {
                            "domain": hostname,
                            "days_left": days_left,
                            "expired": days_left < 0,
                            "expiring_soon": days_left < 30,
                            "issuer": cert.get("issuer", []),
                        }

                        results.append(result)

                        if days_left < 30:
                            logger.warning(
                                f"SSL: {hostname} expira en {days_left} días"
                            )

            except Exception as e:
                logger.error(
                    f"Error verificando SSL de {domain_info.get('domain')}: {e}"
                )
                results.append({"domain": domain_info.get("domain"), "error": str(e)})

        return results

    def check_security(self, node: Dict) -> Dict:
        """
        Analiza auth.log para detectar brute force
        """
        result = {
            "node": node["name"],
            "timestamp": datetime.now().isoformat(),
            "failed_logins": 0,
            "attack_ips": [],
            "security_issues": [],
        }

        ssh_client = self._get_ssh_client(node)
        if not ssh_client:
            result["error"] = "No se pudo conectar SSH"
            return result

        try:
            # Buscar intentos de login fallidos en los últimos 60 minutos
            stdin, stdout, stderr = ssh_client.exec_command(
                "journalctl -u ssh --since '1 hour ago' --no-pager | "
                "grep 'Failed password' | wc -l"
            )
            failed_count = stdout.read().decode().strip()
            result["failed_logins"] = int(failed_count) if failed_count.isdigit() else 0

            if result["failed_logins"] > 10:
                # Obtener IPs atacantes
                stdin, stdout, stderr = ssh_client.exec_command(
                    "journalctl -u ssh --since '1 hour ago' --no-pager | "
                    "grep 'Failed password' | grep -oP '\\d+\\.\\d+\\.\\d+\\.\\d+' | "
                    "sort | uniq -c | sort -rn | head -5"
                )
                ips = stdout.read().decode().strip().split("\n")

                for line in ips:
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            count = int(parts[0])
                            ip = parts[1]
                            if count > 5:
                                result["attack_ips"].append(
                                    {"ip": ip, "attempts": count}
                                )

                if result["attack_ips"]:
                    result["security_issues"].append(
                        "Posible ataque brute force detectado"
                    )
                    logger.warning(
                        f"Security: {node['name']} - {len(result['attack_ips'])} IPs sospechosas"
                    )

        except Exception as e:
            logger.error(f"Error en check_security de {node['name']}: {e}")
            result["error"] = str(e)
        finally:
            ssh_client.close()

        # Guardar resultado
        security_file = self.results_dir / f"{node['name']}_security.json"
        with open(security_file, "w") as f:
            json.dump(result, f, indent=2)

        return result

    def check_disk_growth(self, node: Dict) -> Dict:
        """
        Compara uso de disco con registro anterior
        """
        ssh_client = self._get_ssh_client(node)
        if not ssh_client:
            return {"error": "No SSH connection"}

        try:
            # Obtener uso actual de disco
            stdin, stdout, stderr = ssh_client.exec_command(
                "df -h | grep -v tmpfs | grep -v loop | awk '{print $6\":\"$5}'"
            )
            disks = stdout.read().decode().strip().split("\n")

            current_data = {}
            for disk in disks:
                if ":" in disk:
                    path, pct = disk.split(":")
                    current_data[path] = int(pct.rstrip("%"))

            # Comparar con anterior
            previous = self.previous_disk_data.get(node["name"], {})
            alerts = []

            for path, pct in current_data.items():
                prev_pct = previous.get(path, pct)
                growth = pct - prev_pct

                if growth > 10:
                    alerts.append(f"{path}: +{growth}% esta semana")

            # Guardar datos actuales
            self.previous_disk_data[node["name"]] = current_data
            self._save_disk_data(self.previous_disk_data)

            return {"alerts": alerts, "current": current_data}

        except Exception as e:
            logger.error(f"Error en check_disk_growth: {e}")
            return {"error": str(e)}
        finally:
            ssh_client.close()

    def _get_ssh_client(self, node: Dict) -> Optional[paramiko.SSHClient]:
        """
        Crea cliente SSH conectado al nodo
        """
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Intentar clave SSH
            key_file = node.get("key_file")
            if not key_file:
                key_file = os.path.expanduser("~/.ssh/id_ed25519")
                if not os.path.exists(key_file):
                    key_file = os.path.expanduser("~/.ssh/id_rsa")

            # Si es "via_vps", conectar a través del VPS
            if node.get("password") == "via_vps":
                # Conectar primero al VPS
                vps_config = self._get_vps_config()
                if not vps_config:
                    raise Exception("No hay VPS configurado para proxy")

                # Conectar al VPS
                vps_client = paramiko.SSHClient()
                vps_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                vps_client.connect(
                    vps_config["host"],
                    port=vps_config.get("port", 22),
                    username=vps_config["user"],
                    key_filename=key_file,
                    password=vps_config.get("password"),
                    timeout=10,
                )

                # Ahora ejecutar comando SSH en el VPS para conectar al tunnel
                # Usamos el VPS como jump host
                stdin, stdout, stderr = vps_client.exec_command(
                    f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
                    f"{node['user']}@127.0.0.1 -p {node.get('port', 22)} 'echo connected'"
                )

                # Verificar si funcionó
                result = stdout.read().decode().strip()
                if "connected" in result:
                    # Cerrar VPS client normal y usar command execution instead
                    # Modificamos el cliente para ejecutar comandos via VPS
                    class VPSProxy:
                        def __init__(self, vps_client, node, key_file):
                            self.vps = vps_client
                            self.node = node
                            self.key_file = key_file

                        def exec_command(self, cmd, timeout=30):
                            full_cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {self.node['user']}@127.0.0.1 -p {self.node.get('port', 22)} '{cmd}'"
                            return self.vps.exec_command(full_cmd, timeout=timeout)

                        def close(self):
                            self.vps.close()

                    proxy = VPSProxy(vps_client, node, key_file)
                    # Guardar el proxy como cliente
                    client = proxy
                    return client
                else:
                    raise Exception("No se pudo establecer conexión via tunnel")
            else:
                # Conexión directa
                try:
                    client.connect(
                        node["host"],
                        port=node.get("port", 22),
                        username=node["user"],
                        key_filename=key_file,
                        timeout=10,
                    )
                except:
                    password = node.get("password")
                    if password:
                        client.connect(
                            node["host"],
                            port=node.get("port", 22),
                            username=node["user"],
                            password=password,
                            timeout=10,
                        )
                    else:
                        raise Exception("No se pudo conectar sin contraseña")

            return client

        except Exception as e:
            logger.error(f"Error SSH con {node['name']}: {e}")
            return None

    def _get_vps_config(self) -> Optional[Dict]:
        """Obtiene configuración del VPS para proxy"""
        nodes = load_nodes()
        for node in nodes:
            if node.get("role") == "hub":
                return node
        return None

    def _save_node_status(self, node_name: str, status: Dict):
        """Guarda el estado del nodo en JSON"""
        status_file = self.results_dir / f"{node_name}_latest.json"
        with open(status_file, "w") as f:
            json.dump(status, f, indent=2)

    def execute_command(self, node: Dict, command: str) -> Dict:
        """
        Ejecuta un comando en un nodo remoto
        """
        ssh_client = self._get_ssh_client(node)
        if not ssh_client:
            return {"success": False, "error": "No se pudo conectar"}

        try:
            stdin, stdout, stderr = ssh_client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()

            return {
                "success": not error,
                "output": output,
                "error": error if error else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            ssh_client.close()
