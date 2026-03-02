# Guía de contribución

Gracias por querer contribuir a OpenCode Skills. Esta guía explica cómo añadir nuevas skills o mejorar las existentes.

## Antes de empezar

- Revisa el [catálogo actual](README.md#catálogo-de-skills) para evitar duplicados
- Para skills nuevas, abre un issue primero describiendo qué problema resuelve
- Para mejoras a skills existentes, puedes abrir el PR directamente

## Estructura de una skill válida

```
skills/
└── nombre-skill/
    ├── SKILL.md              ← obligatorio
    └── references/           ← opcional
        └── referencia.md
```

### Requisitos del SKILL.md

El frontmatter es obligatorio y debe incluir:

```yaml
---
name: nombre-skill           # igual que el nombre del directorio
description: |               # 1-1024 caracteres, específico y accionable
  Descripción de cuándo usar esta skill. Sé específico —
  esta descripción determina cuándo OpenCode la activa.
license: MIT
compatibility: opencode
---
```

**Reglas del nombre:**
- Solo minúsculas, números y guiones simples
- Entre 1 y 64 caracteres
- Debe coincidir exactamente con el nombre del directorio
- Válido: `my-skill`, `api-v2`, `db-migrations`
- Inválido: `MySkill`, `my--skill`, `-skill`

### Criterios de calidad

Una skill de calidad:

- **Es específica** — "Úsame cuando el usuario trabaje con migraciones de PostgreSQL" es mejor que "Úsame para base de datos"
- **Tiene ejemplos de código reales** — no pseudocódigo abstracto
- **Incluye lo que NO hacer** — tan importante como lo que SÍ hacer
- **Define cuándo activarse** — sección "Cuándo me activas" con triggers concretos
- **Es autocontenida** — no requiere contexto externo para entenderse

## Flujo de contribución

```bash
# 1. Fork del repositorio
git clone https://github.com/TU_USUARIO/opencode-skills.git
cd opencode-skills

# 2. Crear rama
git checkout -b skill/nombre-de-la-skill

# 3. Crear la skill
mkdir -p skills/nombre-skill
# Editar skills/nombre-skill/SKILL.md

# 4. Verificar que el nombre es válido
echo "nombre-skill" | grep -P '^[a-z0-9]+(-[a-z0-9]+)*$' && echo "✅ Nombre válido" || echo "❌ Nombre inválido"

# 5. Commit con mensaje descriptivo
git commit -m "feat(skills): add nombre-skill skill"

# 6. Push y abrir PR
git push origin skill/nombre-de-la-skill
```

## Descripción del PR

Al abrir el PR, incluye:

```markdown
## Skill añadida/modificada: `nombre-skill`

### ¿Qué hace esta skill?
[Descripción breve]

### ¿Por qué es útil para la comunidad?
[Justificación]

### ¿Cómo la probaste?
[Descripción de las pruebas]

### Checklist
- [ ] El nombre del directorio coincide con `name` en el frontmatter
- [ ] La descripción explica cuándo activarse (no solo qué hace)
- [ ] Incluye ejemplos de código reales
- [ ] Incluye sección "Cuándo me activas" con triggers concretos
- [ ] Sin información propietaria o sensible
```

## Proceso de review

- Un maintainer revisará el PR en un plazo de 7 días
- El criterio principal: ¿sería útil para la comunidad de desarrolladores en general?
- Skills muy específicas de un dominio de negocio particular no serán aceptadas

## Licencia

Al contribuir, aceptas que tu skill se publique bajo la licencia MIT del repositorio.
