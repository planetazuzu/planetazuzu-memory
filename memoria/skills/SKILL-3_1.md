---
name: api-design
description: |
  Diseño de APIs REST, GraphQL y tRPC con criterios profesionales. Úsame cuando el usuario necesite:
  - Diseñar una API nueva desde cero con criterios sólidos
  - Revisar el diseño de endpoints existentes
  - Definir estrategia de versionado y gestión de breaking changes
  - Diseñar paginación, filtrado y ordenación consistentes
  - Establecer el contrato de manejo de errores de la API
  - Decidir entre REST, GraphQL y tRPC según el contexto
  - Diseñar webhooks o APIs de eventos
  - Documentar el contrato de la API (OpenAPI/Swagger)
  Una API bien diseñada es un contrato que dura años. Una mal diseñada es deuda técnica permanente.
license: MIT
compatibility: opencode
metadata:
  audience: backend-developers, architects, tech-leads
  workflow: api-design, rest, graphql, trpc
---

# API Design

## Qué soy

Una API es un contrato público. Una vez que alguien la consume, cambiarla tiene coste. Por eso el diseño importa antes de escribir la primera línea de código.

Yo aplico principios probados de diseño de APIs para que el contrato sea consistente, predecible y duradero — y para que cuando necesite cambiar, lo haga sin romper a los consumidores.

---

## REST vs GraphQL vs tRPC — Cuándo usar cada uno

| | REST | GraphQL | tRPC |
|---|---|---|---|
| **Mejor para** | APIs públicas, múltiples clientes, mobile | Datos complejos relacionados, frontend flexible | Full-stack TypeScript, cliente-servidor mismo repo |
| **Tipado** | Manual (OpenAPI) | Schema propio | TypeScript end-to-end automático |
| **Overfetching** | Problema real | Resuelto por diseño | Resuelto por diseño |
| **Caching** | HTTP nativo | Complejo (Apollo) | Query-level |
| **Curva de aprendizaje** | Baja | Media-alta | Baja si conoces TypeScript |
| **Clientes externos** | ✅ Ideal | ✅ Bien | ❌ Solo TypeScript |
| **Versionado** | `/v1/`, `/v2/` | Evolución del schema | Evolución del router |

**Regla práctica:**
- API pública o múltiples clientes → **REST**
- Frontend con datos complejos y relacionados → **GraphQL**
- Full-stack TypeScript mismo equipo → **tRPC**

---

## REST — Diseño de endpoints

### Nomenclatura de recursos

```
# Recursos en plural, sustantivos, no verbos
✅ GET    /users
✅ GET    /users/:id
✅ POST   /users
✅ PUT    /users/:id
✅ PATCH  /users/:id
✅ DELETE /users/:id

# Relaciones anidadas (máximo 2 niveles)
✅ GET    /users/:id/orders
✅ GET    /orders/:id/items
❌ GET    /users/:id/orders/:orderId/items/:itemId/details  (demasiado anidado)

# Acciones que no son CRUD (usar verbos solo aquí)
✅ POST   /orders/:id/cancel
✅ POST   /users/:id/activate
✅ POST   /emails/verify
```

### HTTP Methods semántica

| Método | Semántica | Idempotente | Body |
|--------|-----------|-------------|------|
| `GET` | Leer | ✅ | No |
| `POST` | Crear / acción | ❌ | Sí |
| `PUT` | Reemplazar completo | ✅ | Sí |
| `PATCH` | Actualización parcial | ❌ | Sí |
| `DELETE` | Eliminar | ✅ | No |

### Códigos de estado correctos

```
# Creación exitosa
201 Created + Location header con la URL del recurso creado

# Operación exitosa sin contenido
204 No Content (DELETE, algunos PATCH)

# Request inválido (validación)
400 Bad Request + cuerpo con detalles del error

# No autenticado (sin token o token inválido)
401 Unauthorized

# Autenticado pero sin permiso sobre el recurso
403 Forbidden

# Recurso no encontrado
404 Not Found

# Conflicto (email duplicado, estado inválido para la operación)
409 Conflict

# Error del servidor
500 Internal Server Error (sin detalles internos)
```

---

## Paginación

### Cursor-based (recomendado para la mayoría de casos)

```typescript
// Request
GET /users?cursor=eyJpZCI6MTAwfQ==&limit=20

// Response
{
  "data": [...],
  "pagination": {
    "cursor": "eyJpZCI6MTIwfQ==",  // cursor para la siguiente página
    "hasMore": true,
    "limit": 20
  }
}
```

**Ventajas sobre offset:** consistente con datos que cambian, no hay páginas duplicadas ni saltadas, funciona con conjuntos de datos grandes.

### Offset-based (solo para UIs con navegación por páginas)

```typescript
// Request
GET /products?page=3&pageSize=20

// Response
{
  "data": [...],
  "pagination": {
    "page": 3,
    "pageSize": 20,
    "total": 847,
    "totalPages": 43,
    "hasNext": true,
    "hasPrev": true
  }
}
```

### Implementación cursor en Prisma

```typescript
async function getUsers(cursor?: string, limit = 20) {
  const decodedCursor = cursor
    ? JSON.parse(Buffer.from(cursor, 'base64').toString())
    : undefined

  const users = await prisma.user.findMany({
    take: limit + 1, // pedir uno más para saber si hay siguiente página
    cursor: decodedCursor ? { id: decodedCursor.id } : undefined,
    skip: decodedCursor ? 1 : 0,
    orderBy: { id: 'asc' },
  })

  const hasMore = users.length > limit
  const data = hasMore ? users.slice(0, -1) : users
  const nextCursor = hasMore
    ? Buffer.from(JSON.stringify({ id: data[data.length - 1].id })).toString('base64')
    : null

  return { data, pagination: { cursor: nextCursor, hasMore, limit } }
}
```

---

## Filtrado y ordenación

```typescript
// Patrón consistente de query params
GET /products?
  status=active&              // filtro simple
  category=electronics&       // filtro simple
  minPrice=100&               // filtro de rango
  maxPrice=500&
  createdAfter=2026-01-01&   // filtro de fecha
  sort=price&                 // campo de ordenación
  order=asc&                  // dirección
  limit=20&
  cursor=xxx

// Implementación con Prisma
const { status, category, minPrice, maxPrice, sort, order } = req.query

const where: Prisma.ProductWhereInput = {
  ...(status && { status }),
  ...(category && { category }),
  ...(minPrice || maxPrice) && {
    price: {
      ...(minPrice && { gte: Number(minPrice) }),
      ...(maxPrice && { lte: Number(maxPrice) }),
    }
  }
}

const orderBy = sort
  ? { [sort as string]: order === 'desc' ? 'desc' : 'asc' }
  : { createdAt: 'desc' }

const products = await prisma.product.findMany({ where, orderBy, ... })
```

---

## Manejo de errores — Contrato estándar (RFC 9457)

RFC 9457 (Problem Details for HTTP APIs) es el estándar moderno. Úsalo:

```typescript
// Estructura estándar de error
interface ApiError {
  type: string      // URI que identifica el tipo de error
  title: string     // Descripción corta del problema
  status: number    // Código HTTP
  detail: string    // Explicación para el desarrollador
  instance?: string // URI de la instancia específica del problema
  // Campos adicionales según el tipo de error:
  errors?: ValidationError[]  // para errores de validación
  code?: string               // código interno para el cliente
}

// Ejemplos
// 400 - Validación
{
  "type": "https://api.ejemplo.com/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "One or more fields failed validation",
  "errors": [
    { "field": "email", "message": "Must be a valid email address" },
    { "field": "name", "message": "Must be between 2 and 100 characters" }
  ]
}

// 404 - Not Found
{
  "type": "https://api.ejemplo.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "User with id 'usr_123' was not found",
  "instance": "/users/usr_123"
}

// 409 - Conflict
{
  "type": "https://api.ejemplo.com/errors/conflict",
  "title": "Email Already Registered",
  "status": 409,
  "detail": "The email 'user@ejemplo.com' is already associated with an account",
  "code": "EMAIL_ALREADY_EXISTS"
}
```

```typescript
// Implementación en Express
class ApiError extends Error {
  constructor(
    public status: number,
    public type: string,
    public title: string,
    public detail: string,
    public extra?: Record<string, unknown>
  ) {
    super(detail)
  }
}

// Middleware de error centralizado
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err instanceof ApiError) {
    return res.status(err.status).json({
      type: err.type,
      title: err.title,
      status: err.status,
      detail: err.detail,
      instance: req.path,
      ...err.extra
    })
  }

  // Error inesperado — no exponer detalles
  logger.error('Unhandled error', { error: err, path: req.path })
  return res.status(500).json({
    type: 'https://api.ejemplo.com/errors/internal',
    title: 'Internal Server Error',
    status: 500,
    detail: 'An unexpected error occurred'
  })
})
```

---

## Versionado

### URL versioning (más común, más claro)
```
/api/v1/users
/api/v2/users
```

### Header versioning (más limpio, menos visible)
```
GET /api/users
API-Version: 2
```

### Cuándo hacer breaking change vs deprecación

**Breaking changes** (requieren nueva versión):
- Eliminar un campo de la respuesta
- Cambiar el tipo de un campo
- Cambiar la semántica de un endpoint
- Eliminar un endpoint

**Non-breaking changes** (se pueden hacer en la versión actual):
- Añadir campos opcionales a la respuesta
- Añadir endpoints nuevos
- Añadir parámetros opcionales

### Ciclo de vida de versiones

```
v1 → active
v2 → active (nueva versión)
v1 → deprecated (con fecha de sunset en header)
     Deprecation: Sat, 01 Jan 2027 00:00:00 GMT
     Sunset: Sat, 01 Jul 2027 00:00:00 GMT
v1 → retired (después de la fecha de sunset)
```

---

## tRPC — Diseño de routers

```typescript
// server/routers/users.ts
import { z } from 'zod'
import { router, protectedProcedure, publicProcedure } from '../trpc'

export const usersRouter = router({
  // Query — equivalente a GET
  list: protectedProcedure
    .input(z.object({
      cursor: z.string().optional(),
      limit: z.number().min(1).max(100).default(20),
      status: z.enum(['active', 'inactive']).optional(),
    }))
    .query(async ({ ctx, input }) => {
      return getUsersWithPagination(input)
    }),

  byId: protectedProcedure
    .input(z.object({ id: z.string().cuid() }))
    .query(async ({ ctx, input }) => {
      const user = await ctx.db.user.findUnique({ where: { id: input.id } })
      if (!user) throw new TRPCError({ code: 'NOT_FOUND' })
      return user
    }),

  // Mutation — equivalente a POST/PUT/PATCH/DELETE
  create: protectedProcedure
    .input(z.object({
      email: z.string().email(),
      name: z.string().min(2).max(100),
      role: z.enum(['admin', 'editor', 'viewer']).default('viewer'),
    }))
    .mutation(async ({ ctx, input }) => {
      return ctx.db.user.create({ data: input })
    }),

  update: protectedProcedure
    .input(z.object({
      id: z.string().cuid(),
      name: z.string().min(2).max(100).optional(),
      role: z.enum(['admin', 'editor', 'viewer']).optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      const { id, ...data } = input
      return ctx.db.user.update({ where: { id }, data })
    }),
})
```

---

## Webhooks — Diseño seguro

```typescript
// Payload estándar de webhook
{
  "id": "evt_01HXYZ",              // ID único del evento — para idempotencia
  "type": "order.completed",       // tipo en formato resource.action
  "createdAt": "2026-02-24T10:00:00Z",
  "data": {
    "object": { /* el recurso completo */ }
  },
  "apiVersion": "2026-02"          // versión de la API que generó el evento
}

// Verificación de firma en el receptor
app.post('/webhooks/stripe', express.raw({ type: 'application/json' }), (req, res) => {
  const sig = req.headers['stripe-signature']

  let event
  try {
    event = stripe.webhooks.constructEvent(req.body, sig, process.env.WEBHOOK_SECRET)
  } catch (err) {
    return res.status(400).send(`Webhook Error: ${err.message}`)
  }

  // Idempotencia — verificar que no procesamos el mismo evento dos veces
  const alreadyProcessed = await db.processedWebhook.findFirst({
    where: { eventId: event.id }
  })
  if (alreadyProcessed) return res.json({ received: true })

  // Procesar el evento de forma asíncrona
  await queue.add('process-webhook', event)

  // Responder 200 inmediatamente — no esperar al procesamiento
  return res.json({ received: true })
})
```

---

## Cuándo me activas

- "Diseña la API para este recurso"
- "¿REST, GraphQL o tRPC para este proyecto?"
- "¿Cómo diseño la paginación de este endpoint?"
- "Define el contrato de errores de la API"
- "¿Cómo versiono esta API sin romper clientes?"
- "Revisa si este diseño de API es correcto"
- "Crea el schema OpenAPI para estos endpoints"
- "¿Cómo diseño los webhooks de forma segura?"
