---
name: context-injection
description: |
  Carga de contexto relevante del proyecto al agente. Úsame cuando el usuario necesite:
  - Que el agente entienda la estructura del proyecto antes de tocar código
  - Cargar documentación de APIs externas o internas sin que el agente las invente
  - Proveer el esquema de base de datos para que las queries sean correctas
  - Inyectar convenciones, glosario de dominio o reglas de negocio al contexto
  - Dar al agente visibilidad de múltiples archivos relacionados antes de hacer un cambio
  - Cargar el historial de decisiones (ADRs) para que el agente no contradiga lo ya decidido
  - Hacer que el agente conozca las dependencias del proyecto antes de sugerir librerías
  Un agente con contexto correcto no inventa — trabaja sobre la realidad del proyecto.
license: MIT
compatibility: opencode
metadata:
  audience: developers, tech-leads, architects
  workflow: context, documentation, codebase-understanding
---

# Context Injection

## Qué soy

El mayor problema de los agentes de IA trabajando en proyectos reales no es la inteligencia — es el contexto. Un agente sin contexto inventa interfaces que no existen, sugiere librerías que ya tienes, y propone soluciones que contradicen decisiones que el equipo tomó hace seis meses.

Yo soluciono eso. Mi trabajo es **cargar el conocimiento correcto antes de actuar**, para que cada respuesta del agente esté anclada en la realidad del proyecto.

---

## Protocolo de carga de contexto

Antes de realizar cualquier tarea sobre el proyecto, sigo este orden:

### Paso 1 — Orientación estructural

Entender el mapa del proyecto antes de tocar nada:

```bash
# Ver la estructura de alto nivel
find . -type f -name "*.ts" | head -50
ls -la src/

# Entender el punto de entrada
cat package.json | jq '{name, version, scripts, dependencies}'

# Ver la configuración del proyecto
cat tsconfig.json
cat .eslintrc.* 2>/dev/null || cat eslint.config.*
```

Lo que busco:
- ¿Cuál es la arquitectura? (monolito, módulos, microservicios)
- ¿Qué framework y versión?
- ¿Cuáles son los scripts disponibles?
- ¿Qué dependencias ya están instaladas?

### Paso 2 — Esquema de datos

Antes de escribir cualquier query o modelo:

```bash
# Prisma
cat prisma/schema.prisma

# Drizzle
cat src/db/schema.ts

# TypeORM (entities)
find src -name "*.entity.ts" | xargs cat

# SQL puro
find . -name "*.sql" -path "*/migrations/*" | sort | tail -5 | xargs cat
```

### Paso 3 — Contratos de API existentes

Antes de crear endpoints o clientes:

```bash
# OpenAPI / Swagger
cat openapi.yaml 2>/dev/null || cat swagger.json 2>/dev/null

# tRPC routers
find src -name "*.router.ts" | xargs cat

# Tipos compartidos
cat src/types/index.ts 2>/dev/null
find src -name "*.dto.ts" | head -10 | xargs cat
```

### Paso 4 — Decisiones previas

Antes de proponer cualquier cambio arquitectónico:

```bash
# ADRs
ls docs/architecture/decisions/ 2>/dev/null
cat docs/architecture/decisions/*.md 2>/dev/null

# CHANGELOG para entender evolución
tail -100 CHANGELOG.md 2>/dev/null
```

### Paso 5 — Convenciones activas

```bash
# Ver ejemplos de código existente del mismo tipo
# Si voy a crear un service, leer un service existente
find src -name "*.service.ts" | head -3 | xargs cat

# Si voy a crear un componente, leer uno existente
find src -name "*.tsx" -not -path "*test*" | head -3 | xargs cat
```

---

## Tipos de contexto y cómo cargarlos

### Contexto de esquema de base de datos

Cuando el agente necesita hacer queries o definir modelos, debe conocer el schema completo.

**Plantilla para inyectar schema en el contexto:**
```markdown
## Schema de base de datos actual

```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  role      Role     @default(VIEWER)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  posts     Post[]
}

model Post {
  id        String   @id @default(cuid())
  title     String
  content   String?
  published Boolean  @default(false)
  authorId  String
  author    User     @relation(fields: [authorId], references: [id])
}

enum Role {
  ADMIN
  EDITOR
  VIEWER
}
```

**Restricciones importantes:**
- `email` es único — nunca insertar sin verificar duplicados
- Los posts no tienen delete en cascade — borrar posts antes de borrar users
- `role` tiene default VIEWER — no asumir ADMIN en código nuevo
```

### Contexto de API externa

Cuando el agente va a consumir una API, cargar los endpoints reales:

```markdown
## API de pagos — Stripe (versión utilizada: 2024-11)

### Endpoints que usamos

**Crear PaymentIntent**
```
POST https://api.stripe.com/v1/payment_intents
Authorization: Bearer sk_...
Content-Type: application/x-www-form-urlencoded

amount=1000&currency=eur&automatic_payment_methods[enabled]=true
```

Respuesta:
```json
{
  "id": "pi_xxx",
  "client_secret": "pi_xxx_secret_xxx",
  "status": "requires_payment_method"
}
```

**Nuestro wrapper interno:**
```typescript
// src/services/payments.service.ts
// USAR ESTE WRAPPER, no llamar a Stripe directamente desde los controllers
import { paymentsService } from '@/services/payments.service'

await paymentsService.createIntent({
  amount: 1000,      // en céntimos
  currency: 'eur',
  customerId: user.stripeCustomerId
})
```
```

### Contexto de arquitectura del proyecto

```markdown
## Arquitectura actual — [Nombre del Proyecto]

### Estructura de módulos
```
src/
├── app/                    ← Next.js App Router
│   ├── (auth)/             ← rutas protegidas por auth
│   ├── api/                ← API Routes
│   └── layout.tsx
├── components/
│   ├── ui/                 ← componentes base (shadcn)
│   └── features/           ← componentes de dominio
├── server/
│   ├── actions/            ← Server Actions
│   ├── queries/            ← consultas de BD (read-only)
│   └── mutations/          ← operaciones de escritura
├── lib/
│   ├── db.ts               ← cliente de Prisma (singleton)
│   ├── auth.ts             ← configuración de NextAuth
│   └── utils.ts
└── types/
    └── index.ts            ← tipos compartidos
```

### Reglas que DEBEN respetarse
- Los Server Actions van en `server/actions/` — nunca inline en componentes
- El cliente de Prisma es singleton en `lib/db.ts` — nunca instanciar `new PrismaClient()` en otro sitio
- Los componentes en `components/ui/` son sin lógica de negocio — solo presentación
- Las queries de BD solo en `server/queries/` — nunca en componentes cliente
```

### Contexto de glosario de dominio

Crítico para proyectos con terminología específica de negocio:

```markdown
## Glosario del dominio — [Nombre del Proyecto]

| Término en el código | Significado en el negocio | Notas |
|---------------------|--------------------------|-------|
| `Subscription` | Contrato de suscripción activo del cliente | NO es lo mismo que `Plan` |
| `Plan` | Definición del producto ofertado (precio, features) | Inmutable una vez creado |
| `Workspace` | Cuenta de organización (puede tener múltiples usuarios) | Un User puede pertenecer a varios Workspaces |
| `Member` | Usuario dentro de un Workspace con un rol específico | La tabla es `workspace_members` |
| `Seat` | Unidad de facturación por usuario activo en un Workspace | |
| `Trial` | Período de prueba antes de que empiece la suscripción | Máximo 14 días |

**Confusiones habituales a evitar:**
- `User` ≠ `Member`. Un User es una identidad global. Un Member es un User en el contexto de un Workspace.
- `cancel` ≠ `deactivate`. Cancel es acción del cliente (fin de periodo). Deactivate es acción admin (inmediata).
```

---

## Archivos de contexto reutilizables

### CONTEXT.md — Archivo de contexto del proyecto

Crear un `CONTEXT.md` en la raíz del proyecto que el agente puede leer al inicio de cualquier sesión:

```markdown
# Contexto del proyecto — [Nombre]

## En una frase
[Qué hace el proyecto y para quién]

## Stack completo
- Runtime: Node.js 22 + TypeScript 5.4
- Framework: Next.js 15 (App Router)
- Base de datos: PostgreSQL 15 + Prisma 5
- Auth: NextAuth v5
- UI: shadcn/ui + Tailwind CSS 4
- Testing: Vitest + Playwright
- Deploy: Vercel (app) + Supabase (BD)

## Estructura de carpetas (resumen)
[árbol simplificado de src/]

## Convenciones críticas
1. [Convención más importante]
2. [Segunda convención]
3. [Tercera convención]

## Lo que NO hacer
- No instalar [librería X] — ya tenemos [alternativa Y]
- No crear nuevos clientes de BD — usar `lib/db.ts`
- No poner lógica en componentes — ir a `server/actions/`

## Decisiones de arquitectura tomadas
- Usamos tRPC en lugar de REST para endpoints internos (ver ADR-003)
- Autenticación con NextAuth, no con Supabase Auth (ver ADR-007)
- Sin Redux ni Zustand — estado de servidor con React Query (ver ADR-009)

## Personas de contacto por área
- Base de datos / migraciones: @nombre
- Auth / seguridad: @nombre
- Pagos / Stripe: @nombre
```

---

## Cuándo el contexto evita errores críticos

### Sin contexto (peligroso)
```
Usuario: "Añade el campo phone al usuario"

Agente sin contexto:
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
// Crea una migración que puede entrar en conflicto con otra en curso
// No sabe que ya existe una migración pendiente de review
// No sabe que phone debería ir en user_profiles, no en users
```

### Con contexto (correcto)
```
Agente con contexto (schema + ADRs + estructura):
1. Lee prisma/schema.prisma → ve que existe UserProfile relacionado
2. Lee ADR-012 → "datos personales adicionales van en UserProfile"
3. Lee migraciones pendientes → hay una en review que toca la misma tabla
4. Propone: añadir phone a UserProfile, coordinar con la migración en curso
```

---

## Cuándo me activas

- "Empieza a trabajar en este proyecto"
- "Necesito que entiendas la estructura antes de hacer cambios"
- "¿Qué hay en este codebase?"
- "Antes de tocar nada, lee el contexto del proyecto"
- "Trabaja con nuestra API de pagos"
- "Usa nuestro schema de BD para escribir esta query"
- "No inventes interfaces — lee las que ya existen"
- "¿Por qué el proyecto está estructurado así?"
