---
name: nextjs-fullstack-best-practices
description: >
  Guía de buenas prácticas para proyectos Next.js 15 (App Router) + TypeScript +
  Tailwind + Shadcn/ui + Dexie.js + PostgreSQL + Genkit (Gemini) + NextAuth + JWT.
  Cubre estructura de repositorio GitHub, limpieza de código, arquitectura de capas,
  convenciones de naming, y flujo de trabajo en equipo.
---

# Buenas Prácticas: Stack Next.js 15 Fullstack

## Stack de referencia

| Capa | Tecnología |
|------|-----------|
| Framework | Next.js 15 (App Router) |
| Lenguaje | TypeScript |
| Estilos | Tailwind CSS |
| UI | Shadcn/ui |
| BD local (caché/offline) | Dexie.js (IndexedDB) |
| BD servidor (fuente de verdad) | PostgreSQL |
| IA | Genkit (Google Gemini) |
| Auth | JWT + NextAuth (Auth.js v5) |

**Premisa fundamental**: PostgreSQL es la fuente de verdad. Dexie.js actúa como caché local / soporte offline. Cualquier dato crítico debe existir en el servidor.

---

## 1. Estructura del repositorio

```
my-app/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # Lint, type-check, tests en cada PR
│   │   └── deploy.yml          # Deploy en merge a main
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
│
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # Grupo de rutas protegidas
│   │   │   ├── dashboard/
│   │   │   └── settings/
│   │   ├── (public)/           # Rutas públicas
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── api/                # Route Handlers
│   │   │   └── [...]/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── loading.tsx
│   │   ├── error.tsx
│   │   └── not-found.tsx
│   │
│   ├── components/
│   │   ├── ui/                 # Componentes de Shadcn (no tocar la base)
│   │   ├── common/             # Componentes reutilizables propios
│   │   └── features/           # Componentes específicos de dominio
│   │       ├── auth/
│   │       ├── dashboard/
│   │       └── [feature]/
│   │
│   ├── lib/
│   │   ├── db/
│   │   │   ├── index.ts        # Cliente PostgreSQL (Drizzle o Prisma)
│   │   │   ├── schema.ts       # Definición de tablas
│   │   │   └── migrations/
│   │   ├── dexie/
│   │   │   ├── db.ts           # Instancia y schema de Dexie
│   │   │   └── sync.ts         # Lógica de sincronización con servidor
│   │   ├── genkit/
│   │   │   ├── client.ts       # Configuración de Genkit
│   │   │   └── flows/          # Flujos de IA (uno por archivo)
│   │   ├── auth/
│   │   │   ├── config.ts       # Configuración de NextAuth
│   │   │   └── utils.ts
│   │   └── utils/
│   │       ├── cn.ts           # Utilidad clsx + tailwind-merge
│   │       └── format.ts       # Formateo de fechas, monedas, etc.
│   │
│   ├── hooks/                  # Custom hooks de React
│   ├── stores/                 # Estado global (Zustand o similar)
│   ├── types/                  # Tipos TypeScript globales
│   │   ├── api.ts
│   │   ├── db.ts
│   │   └── index.ts
│   └── middleware.ts            # Protección de rutas con NextAuth
│
├── public/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env.example                # NUNCA .env en el repo
├── .env.local                  # En .gitignore
├── .eslintrc.json
├── .prettierrc
├── .gitignore
├── commitlint.config.js
├── drizzle.config.ts           # o prisma/schema.prisma
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
├── README.md
└── CONTRIBUTING.md
```

---

## 2. Convenciones de naming

### Archivos y carpetas
- **Componentes**: PascalCase → `UserCard.tsx`, `AuthForm.tsx`
- **Hooks**: camelCase con prefijo `use` → `useAuth.ts`, `useDexieSync.ts`
- **Utilidades / helpers**: camelCase → `formatDate.ts`, `validateEmail.ts`
- **Tipos**: PascalCase para interfaces y types → `UserProfile`, `ApiResponse<T>`
- **Constantes**: SCREAMING_SNAKE_CASE → `MAX_RETRIES`, `API_BASE_URL`
- **Carpetas**: kebab-case → `user-profile/`, `ai-flows/`

### Variables y funciones
- Funciones booleanas: prefijo `is`, `has`, `can` → `isAuthenticated`, `hasPermission`
- Handlers de eventos: prefijo `handle` → `handleSubmit`, `handleLogout`
- Funciones async en API: verbos descriptivos → `fetchUserById`, `createSession`

---

## 3. Separación de responsabilidades (arquitectura en capas)

```
Presentación (componentes React)
        ↓
Lógica de negocio (hooks / server actions)
        ↓
Acceso a datos (lib/db + lib/dexie)
        ↓
Base de datos (PostgreSQL / IndexedDB)
```

### Reglas estrictas

**Server Components por defecto**: Solo añadir `"use client"` cuando sea imprescindible (interactividad, hooks de estado, eventos del navegador).

**Server Actions para mutaciones**: Toda escritura a PostgreSQL debe pasar por un Server Action o Route Handler, nunca llamar directamente a la BD desde el cliente.

**Dexie como caché, no como fuente de verdad**:
- Al cargar datos: primero mostrar lo que hay en Dexie, luego actualizar desde el servidor.
- Al escribir datos: primero guardar en PostgreSQL (await), luego actualizar Dexie.
- Nunca confiar en Dexie para datos críticos sin verificar con el servidor.

---

## 4. TypeScript: tipado estricto

`tsconfig.json` mínimo recomendado:
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

### Reglas de tipado
- **Prohibido `any`**: Usar `unknown` y hacer type narrowing. Configurar ESLint para prohibir `any`.
- **Tipos de API centralizados**: Definir en `src/types/api.ts` y reutilizar entre frontend y backend.
- **Inferencia de Drizzle/Prisma**: Usar los tipos inferidos del ORM como fuente de verdad para los tipos de BD.
- **Usar `satisfies`** en lugar de casteos cuando el tipo es conocido.
- **Tipar los `params` y `searchParams`** de las páginas de Next.js explícitamente.

```typescript
// ✅ Bien
type PageProps = {
  params: { id: string }
  searchParams: { page?: string }
}

// ❌ Mal
export default function Page({ params }: any) { ... }
```

---

## 5. Componentes: reglas de limpieza

- **Máximo ~150 líneas por componente**. Si crece más, extraer sub-componentes.
- **Un componente, una responsabilidad**: No mezclar lógica de fetching, UI y estado en el mismo archivo.
- **Props tipadas siempre**: Nunca `{}` o `any` como tipo de props.
- **Evitar prop drilling de más de 2 niveles**: Usar Context o estado global.
- **Nombrar los exports**: Evitar `export default` anónimos, facilita el debugging.

```typescript
// ✅ Bien
export function UserCard({ user, onEdit }: UserCardProps) { ... }

// ❌ Mal
export default ({ user, onEdit }: any) => { ... }
```

---

## 6. Gestión de base de datos

### PostgreSQL con ORM (Drizzle recomendado con este stack)

- **Schema como única fuente de verdad**: Tipos del frontend deben derivarse del schema del ORM.
- **Migraciones versionadas**: Nunca modificar la BD manualmente en producción. Usar `drizzle-kit generate` o `prisma migrate`.
- **Variables de entorno tipadas**: Validar las env vars al arrancar la app con Zod.

```typescript
// src/lib/env.ts
import { z } from 'zod'

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  NEXTAUTH_SECRET: z.string().min(32),
  GEMINI_API_KEY: z.string(),
})

export const env = envSchema.parse(process.env)
```

### Dexie (IndexedDB)

- **Versionar el schema desde el día 1**: Las migraciones de IndexedDB son irreversibles.
- **Prefixar las stores** con el nombre del dominio para evitar colisiones.
- **Limpiar datos obsoletos**: Implementar una estrategia de expiración (TTL) para el caché local.

```typescript
// src/lib/dexie/db.ts
import Dexie, { type Table } from 'dexie'
import type { User, Post } from '@/types/db'

class AppDB extends Dexie {
  users!: Table<User>
  posts!: Table<Post>

  constructor() {
    super('AppDB')
    this.version(1).stores({
      users: '++id, email, updatedAt',
      posts: '++id, userId, createdAt',
    })
  }
}

export const db = new AppDB()
```

---

## 7. Autenticación (NextAuth + JWT)

- **Proteger rutas en middleware.ts**, no componente por componente.
- **Nunca guardar datos sensibles en el JWT** (contraseñas, tokens de terceros).
- **Rotar el `NEXTAUTH_SECRET`** periódicamente en producción.
- **Validar la sesión en Server Actions** antes de cualquier operación de escritura.

```typescript
// src/middleware.ts
import { auth } from '@/lib/auth/config'

export default auth((req) => {
  if (!req.auth && req.nextUrl.pathname.startsWith('/dashboard')) {
    return Response.redirect(new URL('/login', req.url))
  }
})

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
```

```typescript
// En un Server Action - siempre validar sesión
import { auth } from '@/lib/auth/config'

export async function deletePost(postId: string) {
  const session = await auth()
  if (!session?.user) throw new Error('Unauthorized')
  // ... lógica
}
```

---

## 8. Genkit / IA

- **Un archivo por flujo**: `src/lib/genkit/flows/summarize.ts`, `generate-tags.ts`, etc.
- **Definir schemas de entrada/salida con Zod**: Genkit lo soporta nativamente y añade validación.
- **Nunca exponer el flujo directamente desde el cliente**: Siempre pasar por un Server Action o Route Handler.
- **Manejar errores de la IA explícitamente**: Los modelos pueden fallar o devolver respuestas inesperadas.
- **Usar la UI de desarrollo de Genkit** (`genkit start`) para probar flujos antes de integrarlos.

```typescript
// src/lib/genkit/flows/summarize.ts
import { defineFlow } from '@genkit-ai/flow'
import { geminiPro } from '@genkit-ai/googleai'
import { z } from 'zod'

export const summarizeFlow = defineFlow(
  {
    name: 'summarize',
    inputSchema: z.object({ text: z.string().max(10000) }),
    outputSchema: z.object({ summary: z.string() }),
  },
  async ({ text }) => {
    const response = await geminiPro.generate(`Summarize: ${text}`)
    return { summary: response.text() }
  }
)
```

---

## 9. Repositorio GitHub: configuración esencial

### `.gitignore` crítico
```
.env
.env.local
.env.*.local
node_modules/
.next/
dist/
*.log
.DS_Store
```

### `README.md` mínimo obligatorio
```markdown
# Nombre del proyecto

Descripción breve.

## Stack
...tabla del stack...

## Requisitos previos
- Node.js 20+
- PostgreSQL 15+
- Variables de entorno (ver .env.example)

## Instalación
1. `cp .env.example .env.local`
2. `npm install`
3. `npm run db:migrate`
4. `npm run dev`

## Scripts disponibles
- `npm run dev` - Desarrollo
- `npm run build` - Build de producción
- `npm run lint` - Lint
- `npm run type-check` - Chequeo de tipos
- `npm run db:migrate` - Ejecutar migraciones
- `npm run db:studio` - Abrir Drizzle Studio / Prisma Studio

## Estructura del proyecto
...enlace a docs/architecture.md...
```

### `.env.example` (comprometer en el repo, sin valores reales)
```
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-here-min-32-chars
GEMINI_API_KEY=your-gemini-api-key
```

### Conventional Commits
Usar el estándar de mensajes de commit:
```
feat: añadir autenticación con Google
fix: corregir sincronización de Dexie al volver online
chore: actualizar dependencias
docs: añadir documentación de la API de flujos IA
refactor: extraer lógica de auth a hook separado
test: añadir tests para Server Actions de posts
```

### GitHub Actions CI mínimo
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm run build
```

### Branch strategy recomendada
- `main` → producción (protegida, require PR + review)
- `develop` → integración (opcional para equipos grandes)
- `feat/nombre-feature` → features nuevas
- `fix/nombre-bug` → correcciones

---

## 10. Calidad de código: herramientas obligatorias

### `package.json` scripts mínimos
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "type-check": "tsc --noEmit",
    "format": "prettier --write .",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio"
  }
}
```

### ESLint rules recomendadas
```json
{
  "extends": ["next/core-web-vitals", "next/typescript"],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "prefer-const": "error"
  }
}
```

### Prettier config
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

---

## 11. Checklist de PR (Pull Request Template)

```markdown
## ¿Qué hace este PR?
<!-- Descripción breve -->

## Tipo de cambio
- [ ] feat: nueva funcionalidad
- [ ] fix: corrección de bug
- [ ] refactor: refactorización sin cambios funcionales
- [ ] docs: documentación

## Checklist
- [ ] `npm run type-check` pasa sin errores
- [ ] `npm run lint` pasa sin errores
- [ ] Se han añadido/actualizado tests si aplica
- [ ] Variables de entorno nuevas añadidas a `.env.example`
- [ ] Migraciones de BD incluidas si hay cambios de schema
- [ ] No hay `console.log` de debug olvidados
- [ ] No hay `any` sin justificación documentada
```

---

## Anti-patrones a evitar

| Anti-patrón | Por qué es malo | Alternativa |
|-------------|----------------|-------------|
| Usar `any` en TypeScript | Elimina la seguridad de tipos | `unknown` + type guards |
| Lógica de negocio en componentes | Difícil de testear y reutilizar | Extraer a hooks o Server Actions |
| Llamar a PostgreSQL desde el cliente | Expone credenciales, sin control | Server Actions / Route Handlers |
| Confiar en Dexie como fuente de verdad | Datos desincronizados entre dispositivos | PostgreSQL como master, Dexie como caché |
| Variables de entorno hardcodeadas | Seguridad y portabilidad | `.env.local` + validación con Zod |
| Commits grandes y sin mensaje claro | Historial ilegible, difícil de revertir | Conventional Commits pequeños y atómicos |
| Importar Shadcn como librería externa | Imposible customizar | Copiar componentes a `/components/ui` |
| Exponer flujos de Genkit directamente | Sin autenticación, sin control de costos | Server Actions con validación de sesión |
