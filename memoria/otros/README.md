# Skills de Claude.ai convertidas para OpenCode

Estos archivos son versiones adaptadas de los skills de Claude.ai, listas para usar con OpenCode.

## Skills incluidas

| Skill | Descripción |
|-------|-------------|
| `docx` | Crear, leer y editar documentos Word (.docx) |
| `frontend-design` | Interfaces web production-grade con diseño distintivo |
| `pdf` | Manipular PDFs: leer, fusionar, dividir, OCR, formularios |
| `pptx` | Presentaciones PowerPoint: crear, editar, extraer |
| `xlsx` | Hojas de cálculo Excel: crear, editar, limpiar datos |

## Instalación

### Opción A — Proyecto local

Copia las carpetas dentro de tu repositorio:

```
tu-proyecto/
└── .opencode/
    └── skills/
        ├── docx/SKILL.md
        ├── frontend-design/SKILL.md
        ├── pdf/SKILL.md
        ├── pptx/SKILL.md
        └── xlsx/SKILL.md
```

### Opción B — Global (disponible en todos tus proyectos)

```bash
mkdir -p ~/.config/opencode/skills
cp -r docx frontend-design pdf pptx xlsx ~/.config/opencode/skills/
```

### Opción C — Compatibilidad con Claude

```bash
mkdir -p ~/.claude/skills
cp -r docx frontend-design pdf pptx xlsx ~/.claude/skills/
```

## Configurar permisos (opcional)

En tu `opencode.json`:

```json
{
  "permission": {
    "skill": {
      "*": "allow"
    }
  }
}
```

## Verificar que funcionan

OpenCode listará las skills disponibles así:

```xml
<available_skills>
  <skill>
    <name>docx</name>
    <description>Create, read, edit, or manipulate Word documents...</description>
  </skill>
  <skill>
    <name>frontend-design</name>
    <description>Create distinctive, production-grade frontend interfaces...</description>
  </skill>
  ...
</available_skills>
```

Si una skill no aparece, verifica que:
- El archivo se llama exactamente `SKILL.md` (mayúsculas)
- El frontmatter incluye `name` y `description`
- El `name` en el frontmatter coincide con el nombre del directorio
