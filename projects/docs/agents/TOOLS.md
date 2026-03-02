# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- vps → 207.180.226.141, user: root
- g1 → planeta@192.168.1.139
- raspberry → pepper@pepper.local

### Nodos del Sistema IA

| Rol | Servidor | Usuario | Estado |
|-----|----------|---------|--------|
| Director (VPS) | 207.180.226.141 | root | Por configurar |
| CTO (HP G1) | planeta@192.168.1.139 | planeta | Listo |
| Marketing (RPi) | pepper@pepper.local | pepper | Por configurar |

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
