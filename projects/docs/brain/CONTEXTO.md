# Sistema de Empresa IA Autónoma Distribuida

## Estructura de Nodos

| Rol | Servidor | Usuario | Estado |
|-----|----------|---------|--------|
| Director (VPS) | 207.180.226.141 | root | ✅ Configurado |
| CTO (HP G1) | 192.168.1.139 | planeta | 🔧 En configuración |
| Marketing (RPi) | pepper@pepper.local | pepper | ⏳ Pendiente |

## Carpetas Compartidas

En el VPS: `/shared/`
- `/shared/memoria/` - Memoria central
- `/shared/proyectos/` - Proyectos compartidos
- `/shared/tareas/` - Cola de tareas
- `/shared/resultados/` - Outputs de agentes
- `/shared/config/` - Configuraciones

## SSH Entre Nodos

- VPS → G1: Configurado (falta añadir clave de G1 a VPS)
- VPS → RPi: Pendiente
- G1 → VPS: Pendiente
- G1 → RPi: Pendiente

## Estado de Servicios

### VPS
- ✅ Ollama (qwen2.5:14b-instruct)
- ✅ OpenClaw (usando modelo local)
- ⚠️ OpenCode (desinstalado, por reinstalar)
- ✅ Docker (Nextcloud, NPM, Portainer)

### G1
- ✅ Ollama (modelo grande corriendo)
- ✅ OpenCode
- ✅ OpenClaw

### RPi
- ✅ Ollama
- ✅ OpenCode
- ✅ OpenClaw

## Tareas Pendientes

1. Crear carpetas compartidas en G1
2. Configurar SSH entre todos los nodos
3. Configurar OpenClaw en G1 con modelo local
4. Montar carpetas compartidas via SSHFS
5. Configurar comunicación entre agentes
