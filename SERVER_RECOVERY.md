# Plan de Recuperación del Servidor Nexus

Este documento describe cómo recuperar el servidor después de una limpieza o formateo.

## Repositorios GitHub

### 1. Memoria y Configuraciones
```bash
# Clonar todo el backup
git clone git@github.com:planetazuzu/planetazuzu-memory.git
cd planetazuzu-memory
```

### 2. Estructura del Repo

```
planetazuzu-memory/
├── memoria/                    # Memoria del servidor
│   ├── skills/               # 18 skills de OpenCode/Claude
│   ├── nexus-os/             # Planes de Nexus OS
│   ├── resumenes/            # Resúmenes de conversaciones
│   ├── otros/                # Varios
│   └── docs/                 # Documentos (PDFs, xlsx)
│
├── mcp-servers/              # MCP Servers
│   ├── linkedin_mcp/         # Automatización LinkedIn
│   ├── mcp-finanzas/         # Finanzas
│   └── server-monitor/       # Monitor de servidor
│
├── sessions/                  # Sesiones de chat
│   ├── session-ses_35b2.md
│   ├── session-ses_3557.md
│   └── memoria_agente.md    # ⚠️ Contiene credenciales
│
├── skills/                    # OpenClaw Skills
│   ├── openclaw/
│   │   ├── openclaw-token-optimizer/
│   │   └── token-manager/
│   └── openclaws-kb/         # 55 skills
│
└── projects/                  # Índice de proyectos
```

## Pasos de Recuperación

### 1. Instalar Dependencias Base

```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar herramientas básicas
apt install -y git curl wget python3 python3-pip nodejs npm docker.io nginx

# Instalar Go
curl -sL https://go.dev/dl/go1.21.5.linux-amd64.tar.gz | tar -C /usr/local -xz
export PATH=$PATH:/usr/local/go/bin

# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 2. Recuperar Configuraciones

```bash
# Copiar configuraciones
cp -r memoria/skills/ ~/.config/opencode/  # Si existe
cp -r memoria/docs/ ~/Documentos/

# Restaurar SSH keys (si tienes backup)
cp backup/ssh_keys/* ~/.ssh/
chmod 600 ~/.ssh/*
```

### 3. Reconstruir MCPs

```bash
# server-monitor (Node.js)
cd mcp-servers/server-monitor
npm install
cp .env.example .env
# Configurar variables de entorno

# linkedin_mcp (Python)
cd ../linkedin_mcp
pip install -r requirements.txt
# Configurar credenciales

# mcp-finanzas (Python)
cd ../mcp-finanzas
pip install -r requirements.txt
# Configurar API keys
```

### 4. Servicios Docker

```bash
# Nextcloud
docker run -d \
  --name nextcloud \
  -p 8080:80 \
  -v nextcloud_data:/data \
  nextcloud:latest

# Portainer
docker run -d \
  --name portainer \
  -p 9000:9000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer-ce:latest
```

### 5. Ollama (IA Local)

```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Instalar modelos
ollama pull qwen3:8b
ollama pull mistral:latest
ollama pull llama3.2:3b
```

### 6. Servicios Python

```bash
# nexus-monitor
cd /opt/nexus-monitor
pip install -r requirements.txt
systemctl enable nexus-monitor

# alert-hub
cd /root/alert_hub
pip install -r requirements.txt
```

## Lista de Verificación

- [ ] Sistema base instalado
- [ ] Docker y Docker Compose
- [ ] Nginx configurado
- [ ] Ollama con modelos
- [ ] MCPs instalados
- [ ] Servicios systemd habilitados
- [ ] Backups de volúmenes restaurados
- [ ] Certificados SSL configurados

## Notas Importantes

### Credenciales (ALMACENAR SEGURO)
- `memoria_agente.md` contiene credenciales sensibles
- `memoria/docs/` contiene documentos personales
- Revisar antes de compartir

### Volúmenes Docker
Los volúmenes deben restaurarse desde backups separados:
- nextcloud_data
- portainer_data
- blackbox_postgres_data
- blackbox_redis_data

## Contacto

- Owner: planetazuzu
- Servidor: Nexus (Hetzner)
- IP: 207.180.226.141

---
*Última actualización: 2026-03-02*
