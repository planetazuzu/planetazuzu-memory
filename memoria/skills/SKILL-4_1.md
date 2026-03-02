---
name: database-design
description: |
  Modelado y diseño de bases de datos con criterios profesionales. Úsame cuando el usuario necesite:
  - Diseñar el modelo de datos de un sistema desde cero
  - Revisar un schema existente en busca de problemas
  - Decidir entre normalización y desnormalización según el caso
  - Diseñar índices correctos para los patrones de acceso del sistema
  - Planificar migraciones sin downtime en producción
  - Diseñar estrategias de particionado y sharding
  - Modelar relaciones complejas (muchos-a-muchos, jerarquías, historial)
  - Elegir entre SQL y NoSQL según el dominio
  El schema es la decisión más difícil de revertir. Diseñarlo bien desde el principio ahorra meses.
license: MIT
compatibility: opencode
metadata:
  audience: backend-developers, architects, data-engineers
  workflow: database, schema-design, migrations
---

# Database Design

## Qué soy

El schema de base de datos es la decisión técnica más costosa de cambiar. Una tabla mal diseñada en producción con datos reales puede costar semanas de migración, horas de downtime y bugs difíciles de diagnosticar.

Yo aplico principios de modelado probados para que el schema sea correcto desde el inicio — y cuando necesite cambiar, lo haga de forma segura.

---

## Principios de diseño

### 1. Modelar el dominio, no la interfaz

El schema representa el dominio del negocio, no las pantallas de la aplicación.

```sql
-- ❌ Schema orientado a la UI — "lo que muestra la pantalla de perfil"
CREATE TABLE user_profile_page (
  user_id UUID,
  display_name TEXT,
  avatar_url TEXT,
  bio TEXT,
  follower_count INT,        -- dato derivado, no debe almacenarse
  following_count INT,       -- dato derivado, no debe almacenarse
  recent_posts TEXT[],       -- relación en array: problema grave
);

-- ✅ Schema orientado al dominio
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  avatar_url TEXT,
  bio TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE follows (
  follower_id UUID NOT NULL REFERENCES users(id),
  following_id UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (follower_id, following_id)
);
-- follower_count se calcula con COUNT(), no se almacena
```

### 2. Datos derivados no se almacenan (salvo optimización justificada)

```sql
-- ❌ Campo derivado almacenado — se desincroniza con los datos reales
ALTER TABLE orders ADD COLUMN item_count INT; -- se puede calcular
ALTER TABLE users ADD COLUMN total_spent DECIMAL; -- se puede calcular

-- ✅ Calculado en la query
SELECT u.*, COUNT(o.id) as order_count, SUM(o.total) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;

-- ✅ Excepción válida: campo desnormalizado con trigger para mantenerlo actualizado
-- Solo cuando la query de cálculo es prohibitivamente lenta
```

### 3. Convenciones de nomenclatura consistentes

```sql
-- Tablas: snake_case, plural, sustantivos
users, orders, order_items, product_categories

-- Columnas: snake_case, singular
user_id, created_at, is_active, first_name

-- Claves primarias: siempre 'id'
id UUID PRIMARY KEY

-- Claves foráneas: {tabla_singular}_id
user_id, order_id, product_id

-- Timestamps: siempre con zona horaria
created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ, deleted_at TIMESTAMPTZ

-- Booleanos: prefijo is_ o has_
is_active, is_verified, has_paid, is_deleted
```

---

## Formas normales — Cuándo aplicar cada una

### Primera Forma Normal (1NF)

Cada celda tiene un valor atómico. Sin arrays, sin grupos repetitivos.

```sql
-- ❌ Violación de 1NF: datos no atómicos
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  product_ids TEXT[],        -- array: violación
  product_names TEXT         -- 'Producto A, Producto B': violación
);

-- ✅ 1NF: tabla separada para items
CREATE TABLE orders (id UUID PRIMARY KEY, ...);
CREATE TABLE order_items (
  id UUID PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES orders(id),
  product_id UUID NOT NULL REFERENCES products(id),
  quantity INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL  -- precio en el momento de compra
);
```

### Segunda y Tercera Forma Normal

```sql
-- ❌ Violación de 3NF: dependencia transitiva
-- city_name depende de zip_code, no de user_id
CREATE TABLE users (
  id UUID PRIMARY KEY,
  zip_code VARCHAR(10),
  city_name TEXT,    -- depende de zip_code, no del usuario
  country TEXT       -- depende de zip_code, no del usuario
);

-- ✅ 3NF: separar
CREATE TABLE zip_codes (
  code VARCHAR(10) PRIMARY KEY,
  city TEXT NOT NULL,
  country TEXT NOT NULL
);
CREATE TABLE users (
  id UUID PRIMARY KEY,
  zip_code VARCHAR(10) REFERENCES zip_codes(code)
);
```

### Cuándo desnormalizar (conscientemente)

```sql
-- Desnormalización válida cuando:
-- 1. La query normalizada es inaceptablemente lenta Y está medido
-- 2. El campo cambia raramente Y hay un mecanismo para mantenerlo actualizado

-- Ejemplo: guardar el precio en order_items (no referenciarlo de products)
CREATE TABLE order_items (
  id UUID PRIMARY KEY,
  order_id UUID REFERENCES orders(id),
  product_id UUID REFERENCES products(id),
  unit_price DECIMAL(10,2) NOT NULL,  -- precio histórico, desnormalizado a propósito
  -- Si fuera una FK al precio actual, el historial sería incorrecto
);
```

---

## Tipos de datos — Elegir correctamente

```sql
-- Identificadores
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
-- O con CUID/ULID para ordenación temporal:
id TEXT PRIMARY KEY DEFAULT ('usr_' || gen_random_uuid()::text)

-- Dinero: NUNCA float (errores de precisión)
price DECIMAL(10, 2)     -- hasta 99,999,999.99
-- O mejor: almacenar en céntimos como INTEGER
price_cents INTEGER NOT NULL  -- 1000 = 10.00 EUR

-- Fechas: siempre con zona horaria
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
-- DATE solo si realmente no importa la hora (cumpleaños, fechas de evento)
birthday DATE

-- Enums: tabla de lookup vs enum de postgres
-- Enum de PostgreSQL: eficiente pero difícil de modificar
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'completed', 'cancelled');
-- Tabla de lookup: más flexible
CREATE TABLE order_statuses (code TEXT PRIMARY KEY, label TEXT NOT NULL);
-- En tablas grandes con muchos valores distintos: mejor tabla de lookup

-- Texto: TEXT sobre VARCHAR salvo restricción de negocio real
name TEXT NOT NULL           -- sin límite arbitrario
zip_code CHAR(5) NOT NULL    -- si siempre son exactamente 5 caracteres
```

---

## Índices — Estrategia completa

```sql
-- Regla: crear índices para los patrones de acceso reales, no "por si acaso"

-- 1. FK siempre indexadas (PostgreSQL no las indexa automáticamente)
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

-- 2. Columnas de filtro frecuente
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_users_email ON users(email); -- UNIQUE ya crea índice

-- 3. Índice compuesto (orden = más selectivo primero)
-- Para: WHERE user_id = ? AND status = ?
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- 4. Índice parcial (para subconjuntos con filtro fijo)
CREATE INDEX idx_orders_pending ON orders(created_at)
WHERE status = 'pending';

-- 5. Índice para ordenación frecuente
CREATE INDEX idx_posts_created_desc ON posts(created_at DESC);

-- 6. Full-text search
CREATE INDEX idx_products_fts ON products
USING GIN (to_tsvector('spanish', name || ' ' || COALESCE(description, '')));

-- Verificar índices no usados (coste sin beneficio)
SELECT indexname, idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public' AND idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

## Relaciones complejas

### Jerarquías (categorías anidadas, comentarios con respuestas)

```sql
-- Adjacency List: simple pero queries recursivas necesarias
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  parent_id UUID REFERENCES categories(id)  -- NULL = categoría raíz
);

-- Consultar árbol completo con CTE recursiva
WITH RECURSIVE category_tree AS (
  -- Caso base: raíz
  SELECT id, name, parent_id, 0 AS depth, ARRAY[id] AS path
  FROM categories WHERE parent_id IS NULL

  UNION ALL

  -- Caso recursivo: hijos
  SELECT c.id, c.name, c.parent_id, ct.depth + 1, ct.path || c.id
  FROM categories c
  JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY path;
```

### Historial de cambios (audit log)

```sql
-- Tabla de historial para cambios importantes
CREATE TABLE order_status_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES orders(id),
  from_status order_status,
  to_status order_status NOT NULL,
  changed_by UUID REFERENCES users(id),
  changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reason TEXT
);

-- Trigger automático para registrar cambios
CREATE OR REPLACE FUNCTION log_order_status_change()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.status IS DISTINCT FROM NEW.status THEN
    INSERT INTO order_status_history (order_id, from_status, to_status, changed_at)
    VALUES (NEW.id, OLD.status, NEW.status, now());
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_status_change
  AFTER UPDATE ON orders
  FOR EACH ROW EXECUTE FUNCTION log_order_status_change();
```

### Soft delete (borrado lógico)

```sql
-- Patrón: deleted_at en lugar de DELETE
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ;

-- Row Level Security para excluir automáticamente registros borrados
CREATE POLICY exclude_deleted ON users
  USING (deleted_at IS NULL);

-- O índice parcial para queries eficientes
CREATE INDEX idx_users_active ON users(email)
WHERE deleted_at IS NULL;
```

---

## Migraciones sin downtime

### Expand-Contract pattern (el más seguro)

```sql
-- OBJETIVO: renombrar la columna 'username' a 'display_name'
-- NO hacer: ALTER TABLE users RENAME COLUMN username TO display_name;
-- (rompe el código que sigue usando 'username' en las apps en ejecución)

-- FASE 1 — Expand (deploy 1): añadir nueva columna
ALTER TABLE users ADD COLUMN display_name TEXT;
-- Código nuevo escribe en AMBAS columnas
-- Código viejo sigue leyendo de 'username'

-- FASE 2 — Migrate (deploy 2 o script): sincronizar datos
UPDATE users SET display_name = username WHERE display_name IS NULL;
ALTER TABLE users ALTER COLUMN display_name SET NOT NULL;
-- Código nuevo lee de 'display_name'
-- Código viejo sigue leyendo de 'username' (ambas tienen datos)

-- FASE 3 — Contract (deploy 3): eliminar columna vieja
ALTER TABLE users DROP COLUMN username;
-- Código viejo ya no existe — solo queda el código nuevo
```

### Añadir índice sin bloquear la tabla

```sql
-- ❌ Bloquea escrituras durante minutos en tablas grandes
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- ✅ CONCURRENTLY: no bloquea, tarda más pero sin impacto en producción
CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id);

-- Nota: CONCURRENTLY no puede ejecutarse dentro de una transacción
-- Debe ser una instrucción standalone
```

### Checklist de migración segura

```markdown
- [ ] La migración es backward-compatible (el código viejo funciona con el schema nuevo)
- [ ] Si añade columna NOT NULL: tiene DEFAULT o se hace en expand-contract
- [ ] Si añade índice en tabla grande: usar CREATE INDEX CONCURRENTLY
- [ ] Si renombra columna/tabla: usar expand-contract (3 deploys)
- [ ] Probada en staging con dump de datos de producción (anonimizado)
- [ ] Tiempo de ejecución estimado con EXPLAIN ANALYZE
- [ ] Si > 1 minuto: ventana de mantenimiento o estrategia alternativa
- [ ] Hay rollback documentado
- [ ] Backup reciente de producción disponible
```

---

## SQL vs NoSQL — Cuándo elegir cada uno

| Criterio | SQL (PostgreSQL) | Document (MongoDB) | Key-Value (Redis) | Column (Cassandra) |
|----------|------------------|-------------------|-------------------|-------------------|
| **Schema** | Rígido, validado | Flexible | Sin schema | Semi-estructurado |
| **Relaciones** | Excelente (JOINs) | Manual | No | No |
| **Consistencia** | ACID | Configurable | Eventual | Eventual |
| **Escalado** | Vertical (+ read replicas) | Horizontal | Horizontal | Horizontal |
| **Búsqueda full-text** | Buena (+ pgvector) | Buena | No | No |
| **Mejor para** | Mayoría de aplicaciones | Catálogos flexibles, CMS | Caché, sesiones, colas | Series temporales, logs |

**Regla general:** usar PostgreSQL por defecto. Añadir Redis para caché/sesiones. Considerar alternativas solo cuando PostgreSQL no puede resolver el problema con su configuración normal.

---

## Cuándo me activas

- "Diseña el schema para este sistema"
- "Revisa este modelo de datos"
- "¿Cómo modelo esta relación muchos-a-muchos?"
- "Necesito añadir esta columna sin downtime"
- "¿Qué índices necesita esta tabla?"
- "El schema está desnormalizado — ¿lo corrijo?"
- "¿SQL o MongoDB para este caso?"
- "¿Cómo renombro esta columna en producción con tráfico activo?"
