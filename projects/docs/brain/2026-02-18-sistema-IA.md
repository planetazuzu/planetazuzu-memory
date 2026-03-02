# Sistema de Empresa IA Autónoma Distribuida

## 📅 Fecha: 2026-02-18

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Nodos配置

| Nodo | Rol | IP | Usuario | Estado |
|------|-----|-----|---------|--------|
| VPS | Director | 207.180.226.141 | root | Activo |
| HP G1 | CTO/Infra | 192.168.1.139 | planeta | Activo |
| RPi | Marketing | pepper@pepper.local | pepper | Sin conexión |

### Servicios por Nodo

**VPS:**
- Docker (Nextcloud, Nginx Proxy Manager, Portainer)
- OpenCode (instalado)
- OpenClaw (modelo: qwen2.5:14b-instruct)
- Ollama

**G1:**
- Ollama (qwen3:8b)
- OpenCode
- OpenClaw

**RPi:**
- Ollama
- OpenCode

---

## 📁 ESTRUCTURA DE CARPETAS

```
/shared/                    # Carpetas compartidas (en VPS)
├── memoria/               # Memoria central
├── proyectos/             # Proyectos compartidos
├── tareas/                # Cola de tareas
├── resultados/            # Outputs de agentes
└── config/                # Configuraciones
```

---

## ✅ TRABAJOS REALIZADOS

1. **Limpieza de servidores:**
   - VPS: Eliminados go/, servidor/, archivos innecesarios
   - G1: Eliminados archivos_brutos/, .aider/, varios .zip
   - RPi: Eliminados node_modules/

2. **Configuración SSH:**
   - ControlMaster configurado en ~/.ssh/sockets/
   - Conexiones persistentes

3. **OpenClaw:**
   - VPS: Cambiado de modelo cloud a qwen2.5:14b-instruct
   - G1: Cambiado a qwen3:8b

4. **OpenCode:**
   - VPS: Reinstalado (tú lo hiciste)
   - G1: Funcionando

---

## ❌ ERRORES TYPESCRIPT - TalentOs

### Errores en dexie.ts:
- Propiedades faltantes en tipos User (name, email, role, department)
- bulkUpdate no existe en Table
- _checkAndAwardModuleBadges no existe en DBProvider
- Arguments mismatch en varias funciones
- Tipos de tabla incorrectos

### Errores en postgres.ts:
- Incompatibilidad de tipos en funciones user
- Variables posiblemente undefined
- ForumMessageWithReplies no existe

### Errores en supabase.ts:
- supabaseClient posiblemente undefined
- Property 'users' no existe en Dexie

---

## 📋 PRÓXIMOS PASOS

1. ⏳ Configurar SSH entre nodos (VPS ↔ G1 ↔ RPi)
2. ⏳ Montar carpetas compartidas /shared en todos
3. ⏳ Configurar multi-agent en OpenClaw
4. ⏳ Red privada entre nodos
5. ⏮️ Arreglar errores TypeScript en TalentOs

---

## 🔧 COMANDOS ÚTILES

```bash
# SSH con socket
ssh -o ControlPath=~/.ssh/sockets/user@host-22 host

# Restart OpenClaw
openclaw gateway restart

# Typecheck
npm run typecheck
```

---

## 📝 NOTAS

- El VPS tiene OpenCode funcionando
- El modelo de TalentOs tiene ~30 errores TypeScript
- La RPi no está accesible actualmente
