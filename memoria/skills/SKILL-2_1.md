---
name: onboarding
description: |
  Generación de todo lo necesario para que un desarrollador nuevo sea productivo rápido.
  Úsame cuando el usuario necesite:
  - Crear o actualizar la guía de onboarding del proyecto
  - Generar el setup local paso a paso desde cero
  - Documentar el mapa del codebase para nuevos miembros
  - Crear el plan de primeras tareas (semana 1, mes 1)
  - Documentar a quién preguntar qué y cómo funciona el equipo
  - Generar checklists de verificación de que el setup está correcto
  - Crear materiales de onboarding para un rol específico (frontend, backend, DevOps)
  Un desarrollador nuevo sin onboarding tarda semanas en ser productivo. Con onboarding bien hecho, días.
license: MIT
compatibility: opencode
metadata:
  audience: tech-leads, engineering-managers, developers
  workflow: onboarding, documentation, team
---

# Onboarding

## Qué soy

El tiempo que tarda un desarrollador nuevo en hacer su primer commit real es un indicador directo de la calidad del onboarding. Si tarda más de una semana, el sistema está fallando — no la persona.

Yo genero todos los materiales necesarios para que ese tiempo sea de días: setup local sin fricción, mapa del codebase, primeras tareas graduadas y claridad sobre cómo funciona el equipo.

---

## Estructura de un onboarding completo

```
docs/onboarding/
├── README.md              ← índice y bienvenida
├── 01-setup-local.md      ← entorno local desde cero
├── 02-architecture.md     ← mapa del sistema
├── 03-first-week.md       ← tareas graduadas semana 1
├── 04-team-guide.md       ← cómo trabaja el equipo
├── 05-tools.md            ← herramientas y accesos
└── checklists/
    ├── setup-checklist.md
    └── first-month.md
```

---

## 01 — Setup local desde cero

Plantilla completa para que cualquier persona llegue a tener el proyecto corriendo:

```markdown
# Setup local — [Nombre del Proyecto]

**Tiempo estimado:** 30-60 minutos  
**Última verificación:** YYYY-MM-DD por [@nombre]

Si algo no funciona, abre un issue en [canal/repo] — no pierdas tiempo bloqueado.

---

## Requisitos previos

Instala estas herramientas antes de empezar:

| Herramienta | Versión mínima | Instrucciones |
|-------------|---------------|---------------|
| Node.js | 20.x | [nvm](https://github.com/nvm-sh/nvm): `nvm install 20` |
| Docker | 24.x | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| Git | 2.40+ | Viene con macOS, `apt install git` en Ubuntu |
| [Herramienta X] | X.X | [enlace] |

Verifica que todo está instalado:
```bash
node --version   # debe ser v20.x.x
docker --version # debe ser 24.x.x
git --version    # debe ser 2.40+
```

---

## Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/org/repo.git
cd repo
```

---

## Paso 2 — Variables de entorno

```bash
cp .env.example .env
```

Ahora edita `.env` y rellena los valores marcados con `# REQUIRED`:

```bash
# Los valores de desarrollo los encuentras en [lugar: Notion/1Password/canal de Slack]
# Pide acceso a [@persona] si no los tienes
```

---

## Paso 3 — Instalar dependencias

```bash
npm install
```

---

## Paso 4 — Levantar servicios de infraestructura

```bash
docker compose up -d
```

Verifica que los servicios están corriendo:
```bash
docker compose ps
# Deberías ver: postgres, redis... en estado "running"
```

---

## Paso 5 — Base de datos

```bash
# Crear el schema
npx prisma migrate dev

# Cargar datos de ejemplo (opcional pero recomendado)
npm run db:seed
```

---

## Paso 6 — Arrancar la aplicación

```bash
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000) — deberías ver [descripción de lo que aparece].

---

## Verificación — ¿Funciona todo?

```bash
# Tests unitarios
npm test

# Tests de integración
npm run test:integration
```

Todos los tests deben pasar en verde. Si alguno falla, consulta [sección de troubleshooting].

---

## Troubleshooting frecuente

### "Cannot connect to database"
```bash
# Verificar que postgres está corriendo
docker compose ps postgres

# Si no está, levantarlo
docker compose up -d postgres

# Reintentar la migración
npx prisma migrate dev
```

### "Port 3000 already in use"
```bash
# Encontrar qué proceso usa el puerto
lsof -i :3000

# Matarlo
kill -9 <PID>
```

### "Module not found"
```bash
# Limpiar y reinstalar
rm -rf node_modules
npm install
```

Si el problema persiste → pregunta en [#canal-ayuda] con el error completo.
```

---

## 02 — Mapa del codebase

```markdown
# Mapa del codebase — [Nombre del Proyecto]

## ¿Qué hace este sistema?

[2-3 frases. Sin marketing. Qué problema resuelve y quién lo usa.]

## Diagrama de alto nivel

[Diagrama Mermaid o imagen de la arquitectura]

## Estructura de carpetas — lo que necesitas saber

```
src/
├── app/                ← [qué contiene, cuándo tocarlo]
│   ├── (auth)/         ← [qué contiene]
│   └── api/            ← [qué contiene]
├── components/
│   ├── ui/             ← Componentes base. Casi nunca los tocas.
│   └── features/       ← Aquí vive la mayoría del trabajo de UI
├── server/
│   ├── actions/        ← Server Actions. Lógica que viene del cliente.
│   └── queries/        ← Lecturas de BD. Solo SELECT, sin side effects.
├── lib/
│   ├── db.ts           ← Cliente de Prisma. No instanciar en otro sitio.
│   └── auth.ts         ← Configuración de autenticación.
└── types/              ← Tipos TypeScript compartidos
```

## Los 5 archivos más importantes

1. **`src/lib/db.ts`** — El cliente de base de datos. Todo acceso a datos pasa por aquí.
2. **`src/lib/auth.ts`** — Configuración de autenticación y sesiones.
3. **`prisma/schema.prisma`** — El modelo de datos. Si quieres entender los datos, empieza aquí.
4. **`src/app/layout.tsx`** — El layout raíz de la aplicación.
5. **`opencode.json`** — Configuración de agentes y permisos.

## Flujos que debes entender antes de tocar código

### 1. Cómo una request llega al servidor
[diagrama o descripción paso a paso]

### 2. Cómo funciona la autenticación
[descripción del flujo de login/sesión]

### 3. Cómo se hacen cambios en la base de datos
[proceso de migración]

## Convenciones que debes conocer desde el día 1

- [Convención crítica 1]
- [Convención crítica 2]
- [Convención crítica 3]

Ver [CONTEXT.md](../../CONTEXT.md) para el contexto completo del proyecto.
```

---

## 03 — Plan de primera semana

```markdown
# Primera semana — [Nombre del Proyecto]

El objetivo de la primera semana no es ser productivo todavía.
Es entender el sistema, conocer al equipo y hacer tu primer deploy real.

---

## Día 1 — Orientación

**Mañana:**
- [ ] Setup local completado y funcionando (ver [01-setup-local.md])
- [ ] Accesos configurados: repositorio, Slack, Linear/Jira, herramientas de equipo
- [ ] 1:1 de bienvenida con tu tech lead
- [ ] Leer [CONTEXT.md](../../CONTEXT.md) — el mapa completo del proyecto

**Tarde:**
- [ ] Leer los últimos 10 PRs mergeados para entender el ritmo del equipo
- [ ] Leer los ADRs más recientes en [docs/architecture/decisions/]
- [ ] Identificar 3 preguntas que tienes después de leer — anótalas

---

## Día 2-3 — Exploración guiada

- [ ] Seguir el flujo de una request desde el cliente hasta la base de datos
- [ ] Entender el modelo de datos leyendo `prisma/schema.prisma`
- [ ] Ejecutar los tests y asegurarte de que entiendes qué prueban
- [ ] Leer el código de un módulo completo de principio a fin
- [ ] **Primera tarea real:** [tarea pequeña y bien definida — bug menor, mejora de docs, etc.]

---

## Día 4-5 — Primer PR

- [ ] Completar la primera tarea y abrir tu primer PR
- [ ] Recibir el primer code review
- [ ] Hacer merge de tu primer cambio a main
- [ ] Celebrar 🎉 — ya has contribuido al proyecto

---

## Semana 2-4 — Rampa

| Semana | Objetivo | Indicador de éxito |
|--------|----------|-------------------|
| 2 | Tareas de complejidad media sin ayuda constante | PR sin bloqueantes |
| 3 | Primera feature completa (front + back + test) | Feature en staging |
| 4 | Code review de PRs de otros | Comentarios con etiquetas de severidad |

---

## Recursos de aprendizaje del proyecto

- [Grabación de demo del producto] — [enlace]
- [Documento de arquitectura] — [enlace]
- [Guía de contribución] — [enlace a CONTRIBUTING.md]
- [Runbook de incidencias] — [enlace]
```

---

## 04 — Guía del equipo

```markdown
# Cómo trabaja el equipo — [Nombre del Proyecto]

## Ritmo de trabajo

| Evento | Cuándo | Duración | Qué es |
|--------|--------|----------|--------|
| Daily standup | Lunes-Viernes 9:30 | 15 min | Estado, bloqueos, prioridades |
| Sprint planning | Lunes (inicio de sprint) | 1h | Compromisos de la semana |
| Sprint review | Viernes (fin de sprint) | 30 min | Demo de lo completado |
| Retro | Cada 2 semanas | 45 min | Mejora del proceso |
| Tech sync | Miércoles 16:00 | 1h | Decisiones técnicas, ADRs |

## Canales de comunicación

| Canal | Para qué | Tiempo de respuesta esperado |
|-------|----------|------------------------------|
| #general | Anuncios del equipo | — |
| #dev | Preguntas técnicas, PRs | < 4 horas |
| #incidents | Incidencias en producción | Inmediato |
| #random | Conversación informal | — |
| DM directo | Urgente + personal | < 2 horas |

**Regla de oro:** si puedes esperar, usa el canal. Si es urgente, menciona a la persona.

## Proceso de PRs

1. **Abrir PR** con descripción completa (qué, por qué, cómo probar)
2. **Asignar reviewers:** mínimo 1, máximo 2
3. **Tiempo de review:** 24 horas hábiles para respuesta inicial
4. **Aprobación:** 1 approval para merge (2 para cambios críticos)
5. **Merge:** el autor hace el merge tras la aprobación
6. **Post-merge:** borrar la rama

## A quién preguntar qué

| Área | Persona | Cómo contactar |
|------|---------|---------------|
| Base de datos / schema | [@nombre] | DM o #dev |
| Infraestructura / deploy | [@nombre] | DM o #dev |
| Autenticación / seguridad | [@nombre] | DM o #dev |
| Producto / requisitos | [@nombre] | DM o #product |
| Bloqueos de cualquier tipo | Tu tech lead | DM |

**Nunca te quedes bloqueado más de 2 horas sin pedir ayuda.**
Pedir ayuda no es signo de debilidad — es eficiencia.

## Cómo se toman decisiones técnicas

- **Decisiones pequeñas** (naming, implementación): en el PR
- **Decisiones de diseño** (nuevo patrón, nueva librería): issue de discusión + Tech Sync
- **Decisiones arquitectónicas** (nuevo servicio, cambio de BD): ADR + Tech Sync + aprobación del tech lead

## Valores técnicos del equipo

1. **Código simple sobre código inteligente** — el que lo lee a las 2AM agradece la simplicidad
2. **Tests antes del merge** — no hay excepciones
3. **PRs pequeños** — < 400 líneas siempre que sea posible
4. **Documentar las decisiones** — si fue difícil de decidir, es difícil de recordar
5. **Hablar de los problemas pronto** — no esperar al viernes para decir que el sprint no va bien
```

---

## 05 — Accesos y herramientas

```markdown
# Accesos necesarios — [Nombre del Proyecto]

Solicita estos accesos el primer día. Tu tech lead puede gestionarlos.

## Accesos de desarrollo

- [ ] **GitHub** — organización [org-name], repositorio [repo-name]
  - Solicitar a: [@admin-github]
- [ ] **Variables de entorno de desarrollo**
  - Están en: [1Password / Notion / Vault / otro]
  - Solicitar acceso a: [@persona]
- [ ] **Base de datos de staging** (solo lectura)
  - Solicitar a: [@dba]

## Herramientas de equipo

- [ ] **Slack** — workspace [nombre]
  - Unirse a: #general, #dev, #incidents, #[equipo]
- [ ] **Linear / Jira** — proyecto [nombre]
  - Solicitar a: [@pm]
- [ ] **Notion / Confluence** — espacio [nombre]
  - Solicitar a: [@tech-lead]

## Herramientas opcionales pero recomendadas

- [ ] **Sentry** — error tracking (solo lectura en producción)
- [ ] **Datadog / Grafana** — métricas (solo lectura)
- [ ] **Figma** — diseños (solo lectura)

## Setup de herramientas locales recomendadas

```bash
# VSCode extensions recomendadas (o instalar desde .vscode/extensions.json)
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension prisma.prisma
code --install-extension bradlc.vscode-tailwindcss

# Git config básica
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
git config --global core.editor "code --wait"
```
```

---

## Cuándo me activas

- "Genera la guía de onboarding del proyecto"
- "Crea el setup local desde cero"
- "Un desarrollador nuevo se une al equipo — prepara los materiales"
- "El onboarding actual está desactualizado, actualízalo"
- "Crea el plan de primera semana para el nuevo miembro"
- "Documenta cómo funciona el equipo"
- "¿Qué accesos necesita alguien que empieza hoy?"
