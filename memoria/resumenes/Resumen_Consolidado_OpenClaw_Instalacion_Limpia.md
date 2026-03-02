
# 🧹 Eliminación Completa y Reinstalación Limpia de OpenClaw en Servidor Ubuntu

## 🎯 1. Objetivo de la conversación

Realizar una desinstalación completa de OpenClaw en un servidor Ubuntu 24.04 LTS y efectuar una reinstalación limpia, solucionando problemas relacionados con binarios, PATH, npm global, conflictos con ClawHub y ejecución del gateway.

---

## 📌 2. Puntos clave tratados

- Desinstalación inicial mediante `openclaw uninstall --all --yes`
- Eliminación manual del CLI global con npm
- Problemas con `PATH` y binarios no detectados
- Confusión entre `openclaw` y `clawhub`
- npm 10.9.4 sin soporte para `npm bin`
- Instalación aparentemente exitosa pero sin creación del binario ejecutable
- Restos en `.bashrc` generando errores de autocompletado
- Necesidad de limpieza completa (nuclear)
- Reinstalación recomendada con npm o pnpm
- Consideración de seguridad en servidor público

---

## 💡 3. Ideas principales y conclusiones

### 🧩 Problema Real Detectado

- El instalador indicaba éxito, pero el binario `openclaw` no se generaba en `/usr/bin`.
- npm global estaba usando prefix `/usr`, pero el paquete no quedaba correctamente instalado.
- Se creó un wrapper manual que terminó apuntando a `clawhub` en lugar de OpenClaw.
- Existían residuos de configuraciones previas en `.bashrc` y systemd.

### ⚠️ Confusión Clave

`openclaw` terminó ejecutando `clawhub` (CLI diferente para skills), lo que generó comandos incompatibles (`config`, `doctor`, `start`, etc.).

### 🧹 Solución Adoptada

Se decidió:

1. Eliminar completamente:
   - openclaw
   - clawhub
   - mcporter
   - binarios en `/usr/bin` y `/usr/local/bin`
   - carpetas en `~/.openclaw`
   - módulos en `/usr/lib/node_modules`
2. Limpiar systemd user.
3. Verificar ausencia total con `which` y `npm list -g`.
4. Reinstalar desde cero con npm o pnpm.
5. Recomendar ejecución bajo usuario no-root o en Docker por seguridad.

### 🔐 Insight Estratégico

En servidores públicos:
- Evitar ejecución como root.
- Preferir usuario dedicado o contenedor Docker.
- Validar binarios después de instalación npm global.
- No confiar únicamente en instaladores shell automáticos.

---

## 📚 4. Recursos y ejemplos compartidos

### Comandos de desinstalación

```bash
npm uninstall -g openclaw
npm uninstall -g clawhub
npm uninstall -g mcporter
rm -f /usr/bin/openclaw
rm -rf ~/.openclaw
```

### Verificación de entorno

```bash
npm list -g --depth=0
which openclaw
type -a openclaw
npm config get prefix
npm root -g
```

### Instalación limpia recomendada

```bash
npm install -g openclaw@latest --omit=dev
```

O alternativa:

```bash
pnpm add -g openclaw
```

---

## ❓ 5. Preguntas pendientes o acciones sugeridas

- Confirmar si tras reinstalación el binario se crea correctamente.
- Decidir si ejecutar OpenClaw:
  - Como servicio systemd
  - En modo foreground
  - Dentro de Docker
  - Bajo usuario dedicado
- Validar que el puerto 18789 esté correctamente gestionado.
- Revisar firewall si se expone gateway.

---

## 📝 6. Notas adicionales

Servidor:
- Ubuntu 24.04.4 LTS
- Node.js v22.22.0
- npm 10.9.4
- Prefijo npm global: `/usr`
- IP pública activa
- 12 contenedores Docker activos

Se detectó que npm 10 ya no soporta `npm bin`, lo que afectó el diagnóstico inicial.

---

Documento generado automáticamente como consolidación estructural de la conversación técnica.
