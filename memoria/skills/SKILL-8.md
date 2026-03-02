---
name: code-cleanup
description: >
  Limpia y refactoriza código caótico generado por herramientas Low-Code/No-Code
  (Lovable, Bolt, Cursor, Bubble, etc.) aplicando las mismas reglas que usaría
  un desarrollador senior. Produce código limpio, estructurado, mantenible y
  predecible sin romper funcionalidad existente.
---

# Code Cleanup Skill

## Propósito

Transformar código caótico (generado por IA, Low-Code o No-Code) en código
limpio y profesional, siguiendo el proceso exacto que usaría un desarrollador
senior. **La prioridad absoluta es no romper funcionalidad existente.**

---

## Fase 0 — ANTES de tocar cualquier línea de código

Esta fase es obligatoria. Nunca saltársela.

### 0.1 — Auditoría inicial

Lee y entiende COMPLETAMENTE el proyecto antes de modificar nada:

```
1. Mapear qué hace cada archivo
2. Identificar puntos de entrada (main, index, App, etc.)
3. Identificar dependencias externas (APIs, librerías, servicios)
4. Detectar lógica de negocio crítica (lo que "hace funcionar" la app)
5. Buscar efectos secundarios ocultos (side effects, globals, mutaciones)
```

### 0.2 — Crear snapshot de seguridad

Antes de cualquier cambio:
```bash
git checkout -b cleanup/pre-audit    # rama de seguridad
git add -A && git commit -m "chore: snapshot before cleanup"
```

Si no hay git inicializado:
```bash
git init
git add -A
git commit -m "chore: initial snapshot of chaotic code"
git checkout -b cleanup/phase-1
```

### 0.3 — Documentar comportamiento actual

Crear `BEHAVIOR_SNAPSHOT.md` describiendo qué hace la app:
- Flujos principales (qué pasa cuando el usuario hace X)
- Datos que entran y salen
- Integraciones externas activas
- Cualquier comportamiento que "funciona pero no sé por qué"

---

## Fase 1 — Diagnóstico del caos

Categorizar los problemas encontrados:

### Problemas de estructura
- [ ] Archivos sin nombre descriptivo (`component1.js`, `utils_final_v3.js`)
- [ ] Lógica de negocio mezclada con UI
- [ ] Funciones de 200+ líneas
- [ ] Archivos de 500+ líneas
- [ ] Código duplicado (copy-paste entre archivos)

### Problemas de legibilidad
- [ ] Variables sin nombre semántico (`data`, `temp`, `x`, `result2`)
- [ ] Sin comentarios en lógica compleja
- [ ] Mezcla de idiomas (español/inglés en nombres)
- [ ] Indentación inconsistente
- [ ] Strings mágicos y números mágicos sin constantes

### Problemas de arquitectura
- [ ] Sin separación de responsabilidades
- [ ] Llamadas a API directas desde componentes UI
- [ ] Estado global sin control
- [ ] Dependencias circulares
- [ ] Sin manejo de errores

### Problemas de seguridad
- [ ] API keys en el código (no en variables de entorno)
- [ ] Sin validación de inputs
- [ ] Datos sensibles en logs

---

## Fase 2 — Plan de limpieza (no improvisar)

Crear `CLEANUP_PLAN.md` con:

```markdown
## Orden de limpieza (de menor a mayor riesgo)

### Semana 1 — Sin riesgo
- Renombrar archivos y variables
- Formatear con Prettier/ESLint
- Eliminar código muerto y console.logs
- Añadir constantes para magic strings/numbers

### Semana 2 — Riesgo bajo
- Dividir funciones largas
- Eliminar duplicados
- Mover tipos/interfaces a archivos dedicados

### Semana 3 — Riesgo medio
- Separar lógica de negocio de UI
- Centralizar llamadas a API en /services
- Añadir manejo de errores

### Semana 4 — Riesgo alto (solo si hay tests)
- Refactorizar arquitectura
- Cambiar patrones de estado
- Reestructurar carpetas
```

**Regla de oro: Un cambio a la vez. Commit por cada cambio verificado.**

---

## Fase 3 — Ejecución de la limpieza

### 3.1 — Nomenclatura

**Archivos:**
```
❌ component1.jsx, utils_final_v2.js, nuevo_archivo_copia.ts
✅ UserProfile.jsx, dateUtils.ts, authService.ts
```

**Variables y funciones:**
```
❌ const d = await getData()
✅ const userProfile = await fetchUserProfile(userId)

❌ function process(x) { ... }
✅ function calculateMonthlyRevenue(transactions) { ... }
```

**Constantes mágicas:**
```
❌ if (status === 3) { ... }
✅ const ORDER_STATUS = { PENDING: 1, PROCESSING: 2, COMPLETED: 3 }
   if (status === ORDER_STATUS.COMPLETED) { ... }
```

### 3.2 — Estructura de carpetas profesional

```
src/
├── core/               ← Lógica de negocio pura (sin dependencias de UI)
│   ├── domain/         ← Entidades y reglas de negocio
│   └── useCases/       ← Casos de uso de la aplicación
├── services/           ← Llamadas a APIs y servicios externos
│   └── api/
├── components/         ← Componentes UI puros (sin lógica de negocio)
│   ├── common/         ← Botones, inputs, cards reutilizables
│   └── features/       ← Componentes específicos de cada feature
├── hooks/              ← Lógica reutilizable (React hooks)
├── utils/              ← Funciones de utilidad puras
├── types/              ← Tipos e interfaces TypeScript
├── constants/          ← Constantes de la aplicación
└── config/             ← Configuración y variables de entorno
```

### 3.3 — Separación de responsabilidades

**Antes (caótico):**
```javascript
// UserProfile.jsx - hace todo a la vez
function UserProfile({ userId }) {
  const [user, setUser] = useState(null)
  
  useEffect(() => {
    fetch(`https://api.example.com/users/${userId}`)
      .then(r => r.json())
      .then(data => {
        // lógica de transformación mezclada con UI
        const processed = data.name.split(' ').map(n => n.toUpperCase())
        setUser({ ...data, displayName: processed.join(' ') })
      })
  }, [])

  return <div>{user?.displayName}</div>
}
```

**Después (limpio):**
```javascript
// services/userService.ts
export const fetchUser = async (userId: string): Promise<User> => {
  const response = await apiClient.get(`/users/${userId}`)
  return response.data
}

// utils/nameUtils.ts
export const formatDisplayName = (fullName: string): string =>
  fullName.split(' ').map(n => n.toUpperCase()).join(' ')

// hooks/useUser.ts
export const useUser = (userId: string) => {
  const [user, setUser] = useState<User | null>(null)
  useEffect(() => {
    fetchUser(userId).then(data => 
      setUser({ ...data, displayName: formatDisplayName(data.name) })
    )
  }, [userId])
  return { user }
}

// components/features/UserProfile.tsx - solo UI
function UserProfile({ userId }: { userId: string }) {
  const { user } = useUser(userId)
  return <div>{user?.displayName}</div>
}
```

### 3.4 — Manejo de errores

Cada llamada externa debe tener manejo de errores:

```javascript
// ❌ Sin manejo de errores
const data = await fetch('/api/users').then(r => r.json())

// ✅ Con manejo de errores
try {
  const data = await userService.fetchAll()
  setUsers(data)
} catch (error) {
  if (error instanceof NetworkError) {
    setError('Sin conexión. Intenta de nuevo.')
  } else {
    setError('Error inesperado. Contacta soporte.')
    logger.error('fetchUsers failed', { error, context: 'UserList' })
  }
}
```

### 3.5 — Variables de entorno

```
❌ const API_KEY = "sk-abc123xyz"  // nunca en el código
✅ const API_KEY = process.env.VITE_API_KEY
```

Crear `.env.example` documentando todas las variables necesarias:
```
VITE_API_URL=https://api.example.com
VITE_API_KEY=your_key_here
```

---

## Fase 4 — Verificación después de cada cambio

Después de CADA cambio significativo:

```
1. ¿La app sigue corriendo sin errores?
2. ¿Los flujos principales siguen funcionando?
3. ¿El código nuevo es más legible que el anterior?
4. ¿Alguien que no conozca el proyecto podría entenderlo?
```

Si la respuesta a cualquiera de las primeras dos es NO → revertir y analizar.

```bash
git diff          # revisar qué cambió
git commit -m "refactor: [descripción específica del cambio]"
```

---

## Fase 5 — Documentación final

Una vez limpio, crear/actualizar:

### README.md
```markdown
# Nombre del Proyecto

## ¿Qué hace?
Descripción en 2-3 líneas.

## Stack
- Frontend: React + TypeScript
- Backend: Node.js + Express
- Base de datos: PostgreSQL

## Instalación
\`\`\`bash
npm install
cp .env.example .env
# Rellenar .env con tus valores
npm run dev
\`\`\`

## Estructura del proyecto
[descripción de carpetas principales]

## Flujos principales
[cómo funciona la app]
```

### Comentarios en código complejo
```javascript
// ⚠️ Este cálculo usa la fecha del servidor, no del cliente,
// porque los usuarios pueden estar en zonas horarias diferentes.
// No cambiar a Date.now() sin coordinar con el backend.
const timestamp = serverTime.toISOString()
```

---

## Reglas absolutas (nunca violar)

1. **Nunca reescribir y limpiar al mismo tiempo.** Son dos tareas distintas.
2. **Un commit por cada cambio lógico verificado.**
3. **Si no entiendes por qué algo funciona, no lo toques todavía.**
4. **La legibilidad es más importante que la elegancia.**
5. **El código más corto no siempre es el mejor.**
6. **Cada función debe hacer UNA sola cosa.**
7. **Los nombres deben explicar el "qué", los comentarios el "por qué".**

---

## Checklist final de calidad

Antes de dar el proyecto por limpio:

- [ ] Cualquier developer puede entender el proyecto en < 30 minutos
- [ ] Sin `console.log` en producción
- [ ] Sin variables `temp`, `data`, `x`, `result` sin contexto
- [ ] Sin funciones de +50 líneas sin justificación
- [ ] Sin API keys en el código
- [ ] Sin código comentado (si no se usa, se elimina)
- [ ] README actualizado y funcional
- [ ] `.env.example` con todas las variables
- [ ] Estructura de carpetas coherente y predecible
- [ ] Manejo de errores en todas las llamadas externas
