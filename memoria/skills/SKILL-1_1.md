---
name: code-review
description: |
  Revisión sistemática de código con criterios expertos. Úsame cuando el usuario necesite:
  - Revisar un PR antes de aprobarlo o pedirlo para revisión
  - Detectar bugs, vulnerabilidades o problemas de rendimiento en código nuevo
  - Evaluar si un cambio respeta las convenciones y arquitectura del proyecto
  - Generar comentarios de review listos para pegar en GitHub/GitLab
  - Hacer self-review antes de abrir un PR
  - Auditar un módulo o archivo sin contexto de PR
  - Priorizar qué problemas son bloqueantes vs mejoras opcionales
  No busco perfección — busco lo que importa: corrección, seguridad, mantenibilidad y consistencia.
license: MIT
compatibility: opencode
metadata:
  audience: developers, tech-leads, senior-engineers
  workflow: code-review, pull-requests, quality
---

# Code Review

## Qué soy

El code review no es encontrar errores — es transferir conocimiento, mantener la calidad del sistema y atrapar antes de producción lo que los tests no pueden detectar.

Un buen review tiene criterios claros, prioridades explícitas y comentarios accionables. No es "esto no me gusta" — es "esto romperá X porque Y, y la solución es Z".

Yo estructuro el review para que cada comentario tenga propósito y cada problema tenga prioridad.

---

## Sistema de prioridades

Todo comentario de review lleva una etiqueta de severidad:

| Etiqueta | Significado | Acción requerida |
|----------|-------------|-----------------|
| 🔴 **BLOCKER** | Bug, vulnerabilidad, pérdida de datos. No mergear. | Cambio obligatorio antes del merge |
| 🟠 **MAJOR** | Problema serio de diseño, rendimiento o mantenibilidad | Cambio muy recomendado, discutir si no |
| 🟡 **MINOR** | Mejora de calidad, convención no seguida | Cambio recomendado, puede ir en follow-up |
| 🔵 **NIT** | Estilo, nomenclatura, preferencia | Opcional, no bloquea el merge |
| 💡 **SUGGESTION** | Alternativa a considerar, no necesariamente mejor | Para reflexión, sin presión |
| ❓ **QUESTION** | Necesito entender el razonamiento antes de opinar | Respuesta necesaria para completar el review |

---

## Protocolo de review

### Fase 1 — Contexto (antes de leer el código)

Antes de revisar una sola línea:

1. ¿Qué problema resuelve este PR? (leer descripción y el issue vinculado)
2. ¿Cuál es el alcance declarado del cambio?
3. ¿Hay ADRs o decisiones previas que afecten este área?
4. ¿Cuánto código cambia? (PRs > 400 líneas merecen dividirse)

### Fase 2 — Vista general (10 minutos)

Antes de entrar en detalle, recorrer el diff completo sin detenerse. Objetivo: entender la estructura del cambio, no los detalles.

Preguntas a responder:
- ¿El enfoque general tiene sentido?
- ¿Hay algo que falta o sobra a nivel de archivos?
- ¿El cambio está en los archivos correctos?

### Fase 3 — Review detallado por categoría

---

## Categorías de review

### 1. Corrección — ¿Funciona bien?

**Bugs lógicos:**
```typescript
// 🔴 BLOCKER: Error off-by-one — el último elemento nunca se procesa
for (let i = 0; i < items.length - 1; i++) {
  process(items[i])
}

// ✅ Correcto
for (let i = 0; i < items.length; i++) {
  process(items[i])
}
```

**Race conditions:**
```typescript
// 🔴 BLOCKER: Race condition — dos requests simultáneos pueden crear
// el mismo usuario si ambos pasan el check antes de que cualquiera inserte
const existing = await db.user.findFirst({ where: { email } })
if (!existing) {
  await db.user.create({ data: { email } }) // puede fallar silenciosamente
}

// ✅ Correcto: usar upsert o unique constraint + manejo de error
try {
  await db.user.create({ data: { email } })
} catch (error) {
  if (isUniqueConstraintError(error)) return await db.user.findFirst({ where: { email } })
  throw error
}
```

**Manejo de errores incompleto:**
```typescript
// 🟠 MAJOR: El error se traga silenciosamente — imposible debuggear en producción
try {
  await sendEmail(user.email)
} catch (e) {
  // nada
}

// ✅ Al menos loggear, idealmente reintent o dead-letter queue
try {
  await sendEmail(user.email)
} catch (error) {
  logger.error('Failed to send email', { userId: user.id, error })
  // decidir si relanzar o continuar según el contexto
}
```

**Null/undefined no manejados:**
```typescript
// 🔴 BLOCKER: Si user es null, esto lanza TypeError en producción
const displayName = user.profile.displayName

// ✅ Defensive access
const displayName = user?.profile?.displayName ?? user.email
```

---

### 2. Seguridad — ¿Es seguro?

**Inyección:**
```typescript
// 🔴 BLOCKER: SQL injection — nunca interpolar inputs de usuario
const query = `SELECT * FROM users WHERE email = '${email}'`

// ✅ Queries parametrizadas siempre
const user = await db.query('SELECT * FROM users WHERE email = $1', [email])
```

**Exposición de datos sensibles:**
```typescript
// 🔴 BLOCKER: El hash de la contraseña llega al cliente
return res.json(user) // user incluye passwordHash

// ✅ Seleccionar explícitamente qué campos retornar
const { passwordHash, ...safeUser } = user
return res.json(safeUser)
```

**Autorización no verificada:**
```typescript
// 🔴 BLOCKER: Cualquier usuario autenticado puede borrar cualquier post
app.delete('/posts/:id', authenticate, async (req, res) => {
  await db.post.delete({ where: { id: req.params.id } })
})

// ✅ Verificar que el recurso pertenece al usuario
app.delete('/posts/:id', authenticate, async (req, res) => {
  const post = await db.post.findFirst({
    where: { id: req.params.id, authorId: req.user.id } // ← scope al usuario
  })
  if (!post) return res.status(404).json({ error: 'Not found' })
  await db.post.delete({ where: { id: post.id } })
})
```

**Secrets en código:**
```typescript
// 🔴 BLOCKER: API key hardcodeada en el código fuente
const client = new StripeClient('sk_live_xxxxxxxxxxxx')

// ✅ Desde variable de entorno validada al arrancar
const client = new StripeClient(env.STRIPE_SECRET_KEY)
```

---

### 3. Rendimiento — ¿Es eficiente?

**N+1 queries:**
```typescript
// 🟠 MAJOR: N+1 — una query por cada usuario
const users = await db.user.findMany()
for (const user of users) {
  user.orders = await db.order.findMany({ where: { userId: user.id } })
}

// ✅ Include en una sola query
const users = await db.user.findMany({
  include: { orders: true }
})
```

**Operaciones costosas en el loop:**
```typescript
// 🟠 MAJOR: bcrypt.compare es costoso — ejecutarlo N veces en el render
{users.map(user => (
  <div key={user.id}>{bcrypt.hashSync(user.name, 10)}</div> // ¿qué?
))}
```

**Falta de índice:**
```sql
-- 🟠 MAJOR: Si esta query se ejecuta frecuentemente, necesita índice
SELECT * FROM orders WHERE customer_email = $1 AND status = 'pending';
-- Necesita: CREATE INDEX idx_orders_email_status ON orders(customer_email, status)
```

**Llamadas síncronas que podrían ser paralelas:**
```typescript
// 🟡 MINOR: Se ejecutan en serie innecesariamente
const user = await getUser(id)
const orders = await getOrders(id)
const preferences = await getPreferences(id)

// ✅ En paralelo — 3x más rápido
const [user, orders, preferences] = await Promise.all([
  getUser(id),
  getOrders(id),
  getPreferences(id)
])
```

---

### 4. Mantenibilidad — ¿Durará bien?

**Función demasiado larga:**
```
🟠 MAJOR: Esta función tiene 120 líneas y hace 4 cosas distintas.
Extraer: validateInput(), transformData(), persistRecord(), notifyUser()
Una función, una responsabilidad.
```

**Magic numbers:**
```typescript
// 🟡 MINOR: ¿Qué significa 86400000?
if (Date.now() - user.lastLogin > 86400000) { ... }

// ✅ Constante con nombre
const ONE_DAY_MS = 24 * 60 * 60 * 1000
if (Date.now() - user.lastLogin > ONE_DAY_MS) { ... }
```

**Duplicación evitable:**
```
🟡 MINOR: Esta lógica de validación de email aparece también en
src/auth/register.ts:45 y src/users/update.ts:78.
Extraer a src/lib/validators/email.ts y reutilizar.
```

**Comentario que miente:**
```typescript
// 🟡 MINOR: El comentario dice "retorna null si no existe"
// pero el código lanza una excepción. Uno de los dos es incorrecto.

// Returns null if user not found
async function getUser(id: string) {
  const user = await db.user.findFirstOrThrow({ where: { id } }) // ← lanza
  return user
}
```

---

### 5. Tests — ¿Está cubierto?

**Falta el caso de error:**
```
🟠 MAJOR: Hay tests para el happy path pero ninguno verifica
qué pasa cuando la base de datos falla o el email es inválido.
Los casos de error son donde más bugs aparecen en producción.
```

**Test que no prueba nada:**
```typescript
// 🟡 MINOR: Este test no verifica el comportamiento — solo que no lanza
it('should create a user', async () => {
  await createUser({ email: 'test@test.com' })
  // sin expect
})

// ✅ Verificar el resultado real
it('should create a user with the given email', async () => {
  const user = await createUser({ email: 'test@test.com' })
  expect(user.email).toBe('test@test.com')
  expect(user.id).toBeDefined()
})
```

---

### 6. Consistencia con el proyecto

**Patrón diferente al resto del código:**
```
🟡 MINOR: El resto de los services usan el patrón Repository
(UserRepository, OrderRepository), pero este servicio accede
directamente a Prisma. Extraer un ProductRepository para
mantener consistencia.
```

**Librería nueva sin justificación:**
```
🟠 MAJOR: Se está importando 'lodash' para usar _.groupBy(),
pero el proyecto usa la convención de no añadir dependencias
sin discusión en equipo. Array.prototype.reduce() puede hacer
lo mismo sin nueva dependencia.
```

---

## Plantilla de comentario de review

Para GitHub / GitLab:

```markdown
🟠 **MAJOR** — Posible N+1 query

Cuando `users` tiene muchos registros, esto ejecuta una query
adicional por cada usuario para obtener sus orders.

**Problema:** Con 1.000 usuarios = 1.001 queries en lugar de 2.

**Solución:**
```typescript
const users = await db.user.findMany({
  include: { orders: { where: { status: 'active' } } }
})
```

Si necesitas más control sobre el fetch de orders, considera
un `dataloader` para este caso.
```

---

## Checklist de self-review (antes de abrir el PR)

```markdown
### Corrección
- [ ] He probado el happy path manualmente
- [ ] He probado los casos de error
- [ ] No hay console.log de debug en el código
- [ ] Los casos edge están cubiertos (null, array vacío, strings vacíos)

### Seguridad
- [ ] No hay secrets en el código
- [ ] Los inputs de usuario están validados
- [ ] Los endpoints verifican autorización, no solo autenticación
- [ ] No hay queries construidas con interpolación de strings

### Rendimiento
- [ ] No hay N+1 queries obvias
- [ ] Las operaciones independientes son paralelas (Promise.all)
- [ ] Las operaciones costosas no están en loops

### Calidad
- [ ] El código nuevo sigue el estilo del código existente
- [ ] No hay funciones de más de 50 líneas sin justificación
- [ ] Los nombres de variables y funciones son descriptivos
- [ ] Los tests cubren happy path y casos de error

### PR
- [ ] La descripción explica QUÉ y POR QUÉ (no cómo)
- [ ] El PR es pequeño (< 400 líneas de cambio real)
- [ ] Si rompe algo, está documentado en la descripción
```

---

## Cuándo me activas

- "Revisa este PR antes de que lo apruebe"
- "Haz el review de este archivo"
- "¿Hay algún problema con este código?"
- "Necesito hacer self-review antes de abrir el PR"
- "¿Es seguro este endpoint?"
- "¿Hay algún bug potencial aquí?"
- "Genera los comentarios de review para GitHub"
