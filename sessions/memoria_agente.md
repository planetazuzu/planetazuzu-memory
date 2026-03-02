# Memoria del Agente - Javier Fernández

## Proyectos Activos

### 1. FinBot MCP (Agente Financiero)
**Ubicación:** `/root/finbot_mcp/`
**Estado:** ✅ Operativo 24/7

#### Componentes:
- **server.py** - MCP server con 11 tools (FastMCP + Pydantic v2)
- **finbot_telegram.py** - Bot de Telegram independiente con 17 comandos + IA
- **cronjobs/alertas.py** - Tareas programadas
- **finanzas.json** - Base de datos financiera

#### Integraciones:
- ✅ Telegram: @AlbertoAsesor_bot (chat_id: 930463010)
- ✅ Google Sheets: 1w_tUSvjZ1lqjL-hihJw83XcsbXoBzeCbLr8X68B1_Fg
- ✅ Google Calendar: planetazuzu@gmail.com
- ✅ Service Account: finbot@finbot-488321.iam.gserviceaccount.com

#### Comandos Telegram (17):
- /gasto, /ingreso, /resumen, /presupuesto, /pagos
- /deudas, /ultimos, /perfil
- /analisis, /ahorro, /tendencia, /suscripciones
- /semanal, /syncsheets, /synccalendar, /ayuda

#### Cronjobs Instalados:
- Resumen semanal: Lunes 9:00
- Alertas de pagos: Diario 8:00
- Sync Calendar: Día 25 10:00
- Sync Sheets: Diario 23:30

#### Situación Financiera (Feb 2025):
- Ingreso nómina: 975.83€/mes
- Compromisos fijos: 3,219.30€/mes
- Déficit estimado: -2,119.30€/mes (CRÍTICO)
- Deuda total: 147,640.46€

---

### 2. Gmail MCP (Gestión de Correo)
**Ubicación:** `/root/gmail_mcp/`
**Estado:** ✅ Construido - Requiere OAuth

#### Servidor HTTP:
- **Puerto:** 31435
- **Archivo:** `server_http.py`
- **Tipo:** FastAPI independiente (no STDIO)

#### Endpoints:
- `GET /health` - Health check
- `POST /execute` - Ejecutar tools
- `GET /auth/status` - Estado autenticación
- `GET /auth/url` - URL OAuth
- `GET /auth/callback` - Callback OAuth
- `POST /auth/token` - Intercambiar código

#### Tools Implementadas:
1. gmail_clasificar_correo - Clasifica 1 correo con IA
2. gmail_clasificar_masivo - Clasifica 1000-2000 correos en lotes de 50
3. gmail_monitorizar_nuevos - Revisa cada 15 min, alerta urgentes
4. gmail_extraer_factura - Extrae datos de facturas a Sheets
5. gmail_resumen_matutino - Resumen diario 8:00 por Telegram

####Etiquetas a usar:
- ÁREA: AREA_FINANZAS, AREA_PERSONAL, AREA_PROFESIONAL, AREA_TECNICA, AREA_APRENDIZAJE
- TIPO: TIPO_FACTURA, TIPO_CONTRATO, TIPO_LEGAL, TIPO_NOTIFICACION, TIPO_ACCESO, TIPO_PROPUESTA, TIPO_RENOVACION, TIPO_REUNION, TIPO_SUSCRIPCION
- ESTADO: ESTADO_PENDIENTE, ESTADO_ESPERANDO, ESTADO_RESUELTO

---

## Configuraciones

### Credenciales Google:
- **Service Account:** finbot@finbot-488321.iam.gserviceaccount.com
- **Sheets ID:** 1w_tUSvjZ1lqjL-hihJw83XcsbXoBzeCbLr8X68B1_Fg
- **Calendar ID:** planetazuzu@gmail.com
- **Token OAuth2 Gmail:** /root/gmail_mcp/token.json

### Variables de Entorno:
```
TELEGRAM_BOT_TOKEN=8764458493:AAGgNOXJq09YpZgoyO8sWb7Opi94jSNrv60
TELEGRAM_CHAT_ID=930463010
GOOGLE_SHEETS_ID=1w_tUSvjZ1lqjL-hihJw83XcsbXoBzeCbLr8X68B1_Fg
GOOGLE_CALENDAR_ID=planetazuzu@gmail.com
```

---

## Próximos Pasos

1. ✅ Completar Gmail MCP - Construido
2. ⏳ Completar OAuth2 para Gmail - Requiere autorización del usuario
3. ✅ Instalar cronjobs de Gmail - Instalados
4. ⏳ Prueba completa de Gmail MCP - Requiere OAuth

---

## Gmail MCP - Detalles Técnicos

### Autenticación OAuth2:
- Credenciales: `/root/gmail_mcp/credentials.json` (a configurar por el usuario)
- Token: `/root/gmail_mcp/token.json`
- scopes: gmail.labels, gmail.modify

### Tools MCP (7):
1. gmail_autenticar - Iniciar flujo OAuth2
2. gmail_intercambiar_codigo - Completar OAuth2
3. gmail_clasificar_correo - Clasifica 1 correo
4. gmail_clasificar_masivo - Clasifica hasta 2000 correos
5. gmail_monitorizar_nuevos - Monitoriza y alerta urgentes
6. gmail_extraer_factura - Extrae facturas a Sheets
7. gmail_resumen_matutino - Resumen diario por Telegram

### Cronjobs:
- Monitorizar: cada 15 minutos
- Resumen: diario 8:00

---

## LinkedIn MCP (En construcción)

**Ubicación:** `/root/linkedin_mcp/`

### Características:
- Playwright para automatización
- Comportamiento humano simulado
- Sesión basada en cookies
- Límite: 50 acciones/día
- Horario: 9:00-20:00

### Tools (8):
1. linkedin_guardar_sesion - Login manual y guardar cookies
2. linkedin_leer_mensajes - Leer mensajes no leídos
3. linkedin_clasificar_mensaje - Clasificar (LEAD, COLABORACION, etc.)
4. linkedin_responder_mensaje - Responder con simulación humana
5. linkedin_ver_notificaciones - Ver notificaciones
6. linkedin_guardar_perfil - Guardar en Sheets
7. linkedin_publicar - Publicar en feed (1/día)
8. linkedin_extraer_leads - Extraer leads a Sheets

### Cronjobs:
- Cada 30 min (9-19h): leer y clasificar
- Diario 9:00: resumen

### Estado: Necesita sesión inicial

---

*Última actualización: 2026-02-24*
