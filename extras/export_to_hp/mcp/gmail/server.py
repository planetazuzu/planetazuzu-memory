#!/usr/bin/env python3
"""
gmail_mcp — MCP Server para gestión de Gmail
Gestiona correos, clasifica con etiquetas y extrae facturas.
"""

import json
import os
import datetime
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP, Context

# ─── Configuración ────────────────────────────────────────────────────────────

TOKEN_PATH = Path("/root/gmail_mcp/token.json")
CREDENTIALS_PATH = Path("/root/gmail_mcp/credentials.json")
TELEGRAM_BOT_TOKEN = "8764458493:AAGgNOXJq09YpZgoyO8sWb7Opi94jSNrv60"
TELEGRAM_CHAT_ID = "930463010"
GOOGLE_SHEETS_ID = "1w_tUSvjZ1lqjL-hihJw83XcsbXoBzeCbLr8X68B1_Fg"

# Cargar service account para Sheets
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Etiquetas del sistema
ETIQUETAS_AREAS = [
    "AREA_FINANZAS", "AREA_PERSONAL", "AREA_PROFESIONAL", 
    "AREA_TECNICA", "AREA_APRENDIZAJE"
]
ETIQUETAS_TIPO = [
    "TIPO_FACTURA", "TIPO_CONTRATO", "TIPO_LEGAL", 
    "TIPO_NOTIFICACION", "TIPO_ACCESO", "TIPO_PROPUESTA",
    "TIPO_RENOVACION", "TIPO_REUNION", "TIPO_SUSCRIPCION"
]
ETIQUETAS_ESTADO = [
    "ESTADO_PENDIENTE", "ESTADO_ESPERANDO", "ESTADO_RESUELTO"
]

# Palabras clave para detección automática de urgencia
URGENTES = [
    "banco", "hacienda", "agencia tributaria", "deuda", "cobro",
    "jurídico", "abogado", "demanda", "sentencia", "multa",
    "seguro", "robo", "fraude", "alerta", "urgente", "importante",
    "card", "visa", "mastercard", "préstamo", "crédito"
]

# ─── Autenticación OAuth2 ───────────────────────────────────────────────────

def load_credentials() -> Optional[Dict]:
    """Carga las credenciales OAuth2 desde credentials.json"""
    if CREDENTIALS_PATH.exists():
        return json.loads(CREDENTIALS_PATH.read_text())
    return None

def save_credentials(creds: Dict):
    """Guarda las credenciales OAuth2"""
    CREDENTIALS_PATH.write_text(json.dumps(creds, indent=2))

def load_token() -> Optional[Dict]:
    """Carga el token de acceso desde token.json"""
    if TOKEN_PATH.exists():
        return json.loads(TOKEN_PATH.read_text())
    return None

def save_token(token: Dict):
    """Guarda el token de acceso"""
    TOKEN_PATH.write_text(json.dumps(token, indent=2))

async def get_gmail_token(http: httpx.AsyncClient, credentials: Dict) -> str:
    """Obtiene un token de acceso válido, refrescando si es necesario"""
    token = load_token()
    
    if not token:
        raise ValueError("No hay token. Necesitas autenticarte primero.")
    
    # Verificar si está cerca de expirar (5 minutos)
    expires_at = token.get("expires_at", 0)
    if datetime.datetime.now().timestamp() >= expires_at - 300:
        # Refrescar token
        resp = await http.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"],
                "refresh_token": token["refresh_token"],
                "grant_type": "refresh_token"
            }
        )
        resp.raise_for_status()
        new_token = resp.json()
        new_token["expires_at"] = datetime.datetime.now().timestamp() + new_token["expires_in"]
        save_token(new_token)
        return new_token["access_token"]
    
    return token["access_token"]

async def crear_etiquetas(http: httpx.AsyncClient, token: str):
    """Crea las etiquetas del sistema si no existen"""
    # Obtener etiquetas existentes
    resp = await http.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/labels",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    existentes = {l["name"]: l["id"] for l in resp.json().get("labels", [])}
    
    # Crear etiquetas que faltan
    todas_etiquetas = ETIQUETAS_AREAS + ETIQUETAS_TIPO + ETIQUETAS_ESTADO
    
    for nombre in todas_etiquetas:
        if nombre not in existentes:
            await http.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/labels",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": nombre}
            )

async def obtener_id_etiquetas(http: httpx.AsyncClient, token: str) -> Dict[str, str]:
    """Obtiene los IDs de todas las etiquetas"""
    resp = await http.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/labels",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    return {l["name"]: l["id"] for l in resp.json().get("labels", [])}

# ─── Helpers IA para clasificación ─────────────────────────────────────────

def inferir_etiquetas(asunto: str, remitente: str, snippet: str) -> Dict[str, str]:
    """Infiere las etiquetas apropiadas para un correo usando reglas"""
    texto = f"{asunto} {remitente} {snippet}".lower()
    
    # Inferir ÁREA
    area = "AREA_PERSONAL"  # Por defecto
    if any(p in texto for p in ["trabajo", "empresa", "cv", "entrevista", "jefe", "compañero"]):
        area = "AREA_PROFESIONAL"
    elif any(p in texto for p in ["factura", "banco", "préstamo", "hipoteca", "inversión", "nómina", "hacienda"]):
        area = "AREA_FINANZAS"
    elif any(p in texto for p in ["github", "codigo", "tech", "developer", "api", "server", "debug"]):
        area = "AREA_TECNICA"
    elif any(p in texto for p in ["curso", "udemy", "coursera", "libro", "aprender", "estudio"]):
        area = "AREA_APRENDIZAJE"
    
    # Inferir TIPO
    tipo = "TIPO_NOTIFICACION"  # Por defecto
    if any(p in texto for p in ["factura", "recibo", "invoice", "importe", "total a pagar"]):
        tipo = "TIPO_FACTURA"
    elif any(p in texto for p in ["contrato", "acuerdo", "términos", "condiciones"]):
        tipo = "TIPO_CONTRATO"
    elif any(p in texto for p in ["legal", "abogado", "demanda", "sentencia"]):
        tipo = "TIPO_LEGAL"
    elif any(p in texto for p in ["acceso", "password", "usuario", "cuenta", "inicio sesión"]):
        tipo = "TIPO_ACCESO"
    elif any(p in texto for p in ["propuesta", "oferta", "presupuesto"]):
        tipo = "TIPO_PROPUESTA"
    elif any(p in texto for p in ["renovación", "renovar", "vencimiento", "caduca"]):
        tipo = "TIPO_RENOVACION"
    elif any(p in texto for p in ["reunión", "meeting", "calendar", "convocatoria"]):
        tipo = "TIPO_REUNION"
    elif any(p in texto for p in ["suscripción", "suscripcion", "suscrito", "premium"]):
        tipo = "TIPO_SUSCRIPCION"
    
    # Inferir ESTADO (por defecto pendiente)
    estado = "ESTADO_PENDIENTE"
    if any(p in texto for p in ["resuelto", "completado", "hecho", "ok", "confirmado"]):
        estado = "ESTADO_RESUELTO"
    elif any(p in texto for p in ["esperando", "pendiente de", "a la espera", "revisando"]):
        estado = "ESTADO_ESPERANDO"
    
    return {"area": area, "tipo": tipo, "estado": estado}

def es_urgente(asunto: str, remitente: str, snippet: str) -> bool:
    """Determina si un correo es urgente"""
    texto = f"{asunto} {remitente} {snippet}".lower()
    return any(p in texto for p in URGENTES)

def extraer_datos_factura(asunto: str, snippet: str) -> Optional[Dict]:
    """Extrae datos de factura del correo"""
    texto = f"{asunto} {snippet}"
    
    # Buscar importe
    importe_match = re.search(r'(\d+[.,]\d{2})\s*€', texto, re.IGNORECASE)
    if not importe_match:
        importe_match = re.search(r'(?:importe|total|amount|cantidad)[:\s]*(\d+[.,]\d{2})', texto, re.IGNORECASE)
    
    if not importe_match:
        return None
    
    # Buscar fecha
    fecha_match = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})', texto)
    
    # Buscar emisor (dominio del email o palabras clave)
    emisor_match = re.search(r'from[:\s]*[<?]?([\w\s]+@[\w.-]+)', texto, re.IGNORECASE)
    
    return {
        "importe": float(importe_match.group(1).replace(",", ".")),
        "fecha": fecha_match.group() if fecha_match else datetime.date.today().isoformat(),
        "emisor": emisor_match.group(1) if emisor_match else "Desconocido",
        "concepto": asunto[:100]
    }

# ─── Lifespan ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Inicializa el servidor y verifica autenticación"""
    async with httpx.AsyncClient(timeout=30.0) as http:
        creds = load_credentials()
        
        if not creds:
            # Guardar credenciales placeholder - el usuario debe proporcionar OAuth
            yield {"http": http, "autenticado": False}
        else:
            try:
                token = await get_gmail_token(http, creds)
                await crear_etiquetas(http, token)
                yield {"http": http, "autenticado": True}
            except Exception as e:
                yield {"http": http, "autenticado": False, "error": str(e)}

mcp = FastMCP("gmail_mcp", lifespan=app_lifespan)

# ─── Modelos de entrada ─────────────────────────────────────────────────────

class ClasificarCorreoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message_id: str = Field(..., description="ID del mensaje de Gmail a clasificar")

class ClasificarMasivoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limite: int = Field(default=100, description="Número de correos a clasificar (max 2000)", ge=1, le=2000)

class ExtraerFacturaInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limite: int = Field(default=50, description="Número de correos a revisar para facturas", ge=1, le=500)

# ─── TOOLS ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def gmail_clasificar_correo(params: ClasificarCorreoInput, ctx: Context) -> str:
    """Clasifica un correo asignándole etiquetas AREA + TIPO + ESTADO.
    
    Analiza el asunto, remitente y contenido para inferir las etiquetas
    correctas usando IA basada en reglas.
    """
    http = ctx.request_context.lifespan_state["http"]
    credentials = load_credentials()
    
    if not credentials:
        return json.dumps({"error": "No hay credenciales OAuth. Ejecuta el flujo de autenticación."})
    
    try:
        token = await get_gmail_token(http, credentials)
        ids_etiquetas = await obtener_id_etiquetas(http, token)
        
        # Obtener detalles del correo
        resp = await http.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{params.message_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp.raise_for_status()
        msg = resp.json()
        
        # Extraer información
        asunto = ""
        remitente = ""
        snippet = msg.get("snippet", "")
        
        for header in msg.get("payload", {}).get("headers", []):
            if header["name"].lower() == "subject":
                asunto = header["value"]
            if header["name"].lower() == "from":
                remitente = header["value"]
        
        # Inferir etiquetas
        etiquetas = inferir_etiquetas(asunto, remitente, snippet)
        
        # Obtener IDs de etiquetas
        label_ids = []
        for key in ["area", "tipo", "estado"]:
            nombre = etiquetas[key]
            if nombre in ids_etiquetas:
                label_ids.append(ids_etiquetas[nombre])
        
        # Aplicar etiquetas
        await http.post(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{params.message_id}/modify",
            headers={"Authorization": f"Bearer {token}"},
            json={"addLabelIds": label_ids}
        )
        
        return json.dumps({
            "clasificado": True,
            "message_id": params.message_id,
            "asunto": asunto,
            "etiquetas_asignadas": etiquetas,
            "urgente": es_urgente(asunto, remitente, snippet)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def gmail_clasificar_masivo(params: ClasificarMasivoInput, ctx: Context) -> str:
    """Clasifica correos existentes en lotes de 50.
    
    Procesa los correos sin clasificar y les asigna etiquetas.
    Reporta el progreso por Telegram al inicio y al final.
    """
    http = ctx.request_context.lifespan_state["http"]
    credentials = load_credentials()
    
    if not credentials:
        return json.dumps({"error": "No hay credenciales OAuth"})
    
    try:
        token = await get_gmail_token(http, credentials)
        ids_etiquetas = await obtener_id_etiquetas(http, token)
        
        # Obtener lista de correos
        resp = await http.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers={"Authorization": f"Bearer {token}"},
            params={"maxResults": params.limite, "q": "-label:AREA_FINANZAS -label:AREA_PERSONAL -label:AREA_PROFESIONAL"}
        )
        resp.raise_for_status()
        mensajes = resp.json().get("messages", [])
        
        if not mensajes:
            return json.dumps({"mensajes": "No hay correos sin clasificar"})
        
        # Enviar mensaje inicial por Telegram
        await http.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"📧 *Clasificando {len(mensajes)} correos...*",
                "parse_mode": "Markdown"
            }
        )
        
        # Procesar en lotes de 50
        clasificados = 0
        errores = 0
        
        for i in range(0, len(mensajes), 50):
            batch = mensajes[i:i+50]
            
            for msg in batch:
                try:
                    # Obtener detalles
                    resp = await http.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    msg_data = resp.json()
                    
                    # Extraer información
                    asunto = ""
                    remitente = ""
                    snippet = msg_data.get("snippet", "")
                    
                    for header in msg_data.get("payload", {}).get("headers", []):
                        if header["name"].lower() == "subject":
                            asunto = header["value"]
                        if header["name"].lower() == "from":
                            remitente = header["value"]
                    
                    # Inferir etiquetas
                    etiquetas = inferir_etiquetas(asunto, remitente, snippet)
                    
                    # Obtener IDs
                    label_ids = []
                    for key in ["area", "tipo", "estado"]:
                        nombre = etiquetas[key]
                        if nombre in ids_etiquetas:
                            label_ids.append(ids_etiquetas[nombre])
                    
                    # Aplicar etiquetas
                    await http.post(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}/modify",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"addLabelIds": label_ids}
                    )
                    
                    clasificados += 1
                    
                except Exception:
                    errores += 1
        
        # Enviar resultado final por Telegram
        await http.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"✅ *Clasificación completada*\n\n"
                        f"• Clasificados: {clasificados}\n"
                        f"• Errores: {errores}",
                "parse_mode": "Markdown"
            }
        )
        
        return json.dumps({
            "total_procesados": len(mensajes),
            "clasificados": clasificados,
            "errores": errores
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def gmail_monitorizar_nuevos(ctx: Context) -> str:
    """Monitorea correos nuevos y los clasifica.
    
    Para uso en cronjob cada 15 minutos. Clasifica correos
    y alerta por Telegram si son urgentes.
    """
    http = ctx.request_context.lifespan_state["http"]
    credentials = load_credentials()
    
    if not credentials:
        return json.dumps({"nuevos": 0, "error": "No autenticado"})
    
    try:
        token = await get_gmail_token(http, credentials)
        ids_etiquetas = await obtener_id_etiquetas(http, token)
        
        # Obtener últimos correos (últimas 2 horas)
        hace_2_horas = int((datetime.datetime.now() - datetime.timedelta(hours=2)).timestamp())
        
        resp = await http.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers={"Authorization": f"Bearer {token}"},
            params={"maxResults": 50, "q": f"after:{hace_2_horas}"}
        )
        resp.raise_for_status()
        mensajes = resp.json().get("messages", [])
        
        if not mensajes:
            return json.dumps({"nuevos": 0, "clasificados": 0})
        
        nuevos_clasificados = 0
        urgentes = []
        
        for msg in mensajes:
            try:
                resp = await http.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                msg_data = resp.json()
                
                # Verificar si ya tiene etiquetas de área
                tiene_area = any(
                    lid in ids_etiquetas.values()
                    for lid in msg_data.get("labelIds", [])
                )
                
                if tiene_area:
                    continue
                
                # Extraer información
                asunto = ""
                remitente = ""
                snippet = msg_data.get("snippet", "")
                
                for header in msg_data.get("payload", {}).get("headers", []):
                    if header["name"].lower() == "subject":
                        asunto = header["value"]
                    if header["name"].lower() == "from":
                        remitente = header["value"]
                
                # Inferir etiquetas
                etiquetas = inferir_etiquetas(asunto, remitente, snippet)
                
                # Obtener IDs
                label_ids = []
                for key in ["area", "tipo", "estado"]:
                    nombre = etiquetas[key]
                    if nombre in ids_etiquetas:
                        label_ids.append(ids_etiquetas[nombre])
                
                # Aplicar etiquetas
                await http.post(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}/modify",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"addLabelIds": label_ids}
                )
                
                nuevos_clasificados += 1
                
                # Si es urgente, añadir a la lista de alerta
                if es_urgente(asunto, remitente, snippet):
                    urgentes.append({"asunto": asunto, "remitente": remitente[:50]})
                
            except Exception:
                pass
        
        # Enviar alerta si hay urgentes
        if urgentes:
            msg_urgentes = "🚨 *Correos urgentes detectados:*\n\n"
            for u in urgentes[:5]:
                msg_urgentes += f"• {u['asunto'][:60]}...\n"
            
            await http.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg_urgentes, "parse_mode": "Markdown"}
            )
        
        return json.dumps({
            "nuevos_procesados": len(mensajes),
            "clasificados": nuevos_clasificados,
            "urgentes": len(urgentes)
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def gmail_extraer_factura(params: ExtraerFacturaInput, ctx: Context) -> str:
    """Extrae datos de facturas de correos y los guarda en Google Sheets.
    
    Busca correos con facturas y extrae: emisor, importe, fecha, concepto.
    Los guarda en la hoja 'Facturas' del Sheets configurado.
    """
    http = ctx.request_context.lifespan_state["http"]
    credentials = load_credentials()
    
    if not credentials:
        return json.dumps({"extracciones": 0, "error": "No autenticado"})
    
    try:
        gmail_token = await get_gmail_token(http, credentials)
        
        # Buscar correos con facturas
        resp = await http.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers={"Authorization": f"Bearer {gmail_token}"},
            params={"maxResults": params.limite, "q": "label:TIPO_FACTURA"}
        )
        resp.raise_for_status()
        mensajes = resp.json().get("messages", [])
        
        if not mensajes:
            # Buscar por keywords
            resp = await http.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers={"Authorization": f"Bearer {gmail_token}"},
                params={"maxResults": params.limite, "q": "factura OR invoice OR recibo"}
            )
            mensajes = resp.json().get("messages", [])
        
        facturas = []
        
        for msg in mensajes[:20]:
            try:
                resp = await http.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                    headers={"Authorization": f"Bearer {gmail_token}"}
                )
                msg_data = resp.json()
                
                asunto = ""
                snippet = msg_data.get("snippet", "")
                
                for header in msg_data.get("payload", {}).get("headers", []):
                    if header["name"].lower() == "subject":
                        asunto = header["value"]
                
                datos = extraer_datos_factura(asunto, snippet)
                if datos:
                    datos["fecha_extraido"] = datetime.date.today().isoformat()
                    datos["message_id"] = msg["id"]
                    facturas.append(datos)
                    
            except Exception:
                pass
        
        if not facturas:
            return json.dumps({"extracciones": 0, "mensaje": "No se encontraron facturas"})
        
        # Guardar en Sheets
        service_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        if not service_json:
            return json.dumps({"extracciones": len(facturas), "error": "No hay service account para Sheets"})
        
        from google.oauth2 import service_account
        import google.auth.transport.requests
        
        creds_info = json.loads(service_json)
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        request = google.auth.transport.requests.Request()
        creds.refresh(request)
        sheets_token = creds.token
        
        # Preparar filas
        filas = [["Fecha", "Emisor", "Importe", "Concepto", "Fecha Extraído"]]
        for f in facturas:
            filas.append([
                f.get("fecha", ""),
                f.get("emisor", ""),
                f.get("importe", 0),
                f.get("concepto", "")[:50],
                f.get("fecha_extraido", "")
            ])
        
        # Escribir en Sheets
        sheets_url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEETS_ID}/values/Facturas!A1?valueInputOption=USER_ENTERED"
        
        # Crear hoja si no existe
        try:
            resp = await http.put(sheets_url, headers={"Authorization": f"Bearer {sheets_token}"}, json={"values": filas})
            if resp.status_code != 200:
                # Crear hoja
                await http.post(
                    f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEETS_ID}:batchUpdate",
                    headers={"Authorization": f"Bearer {sheets_token}"},
                    json={"requests": [{"addSheet": {"properties": {"title": "Facturas"}}}]}
                )
                resp = await http.put(sheets_url, headers={"Authorization": f"Bearer {sheets_token}"}, json={"values": filas})
        except Exception:
            pass
        
        return json.dumps({
            "extracciones": len(facturas),
            "facturas": facturas[:5],
            "sheets_actualizado": True
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def gmail_resumen_matutino(ctx: Context) -> str:
    """Genera y envía un resumen matutino de correos pendientes por Telegram.
    
    Agrupa los correos por AREA y TIPO, mostrando el estado.
    """
    http = ctx.request_context.lifespan_state["http"]
    credentials = load_credentials()
    
    if not credentials:
        return json.dumps({"error": "No autenticado"})
    
    try:
        token = await get_gmail_token(http, credentials)
        
        # Obtener todos los correos pendientes
        resp = await http.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers={"Authorization": f"Bearer {token}"},
            params={"maxResults": 500, "q": "label:ESTADO_PENDIENTE"}
        )
        mensajes = resp.json().get("messages", [])
        
        # Obtener etiquetas
        ids_etiquetas = await obtener_id_etiquetas(http, token)
        
        # Agrupar por área y tipo
        por_area = {}
        por_tipo = {}
        
        for msg in mensajes[:100]:
            try:
                resp = await http.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                msg_data = resp.json()
                
                label_ids = msg_data.get("labelIds", [])
                
                # Encontrar área y tipo
                for nombre, lid in ids_etiquetas.items():
                    if lid in label_ids:
                        if nombre.startswith("AREA_"):
                            por_area[nombre] = por_area.get(nombre, 0) + 1
                        elif nombre.startswith("TIPO_"):
                            por_tipo[nombre] = por_tipo.get(nombre, 0) + 1
                            
            except Exception:
                pass
        
        # Generar mensaje
        msg = "📧 *RESUMEN MATUTINO - Correos Pendientes*\n\n"
        
        msg += "*Por ÁREA:*\n"
        for area, count in sorted(por_area.items(), key=lambda x: -x[1]):
            msg += f"  📁 {area.replace('AREA_', '')}: {count}\n"
        
        msg += "\n*Por TIPO:*\n"
        for tipo, count in sorted(por_tipo.items(), key=lambda x: -x[1]):
            msg += f"  🏷️ {tipo.replace('TIPO_', '')}: {count}\n"
        
        msg += f"\n_Total pendientes: {len(mensajes)}_"
        
        # Enviar por Telegram
        await http.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        )
        
        return json.dumps({
            "enviado": True,
            "pendientes": len(mensajes),
            "por_area": por_area,
            "por_tipo": por_tipo
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── Autenticación OAuth ───────────────────────────────────────────────────

@mcp.tool()
async def gmail_autenticar(credentials_json: str, ctx: Context) -> str:
    """Guarda las credenciales OAuth2 y inicia el flujo de autenticación.
    
    Proporciona un JSON con client_id y client_secret de Google Cloud Console.
    """
    try:
        creds = json.loads(credentials_json)
        if "client_id" not in creds or "client_secret" not in creds:
            return json.dumps({"error": "El JSON debe contener client_id y client_secret"})
        
        save_credentials(creds)
        
        # Generar URL de autorización
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": creds["client_id"],
            "redirect_uri": "http://localhost:8080/callback",
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/gmail.labels https://www.googleapis.com/auth/gmail.modify",
            "access_type": "offline",
            "prompt": "consent"
        })
        
        return json.dumps({
            "estado": "Credenciales guardadas",
            "auth_url": auth_url,
            "instrucciones": "1. Visita la URL\n2. Autoriza la app\n3. Copia el código\n4. Usa gmail_intercambiar_codigo con el código"
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def gmail_intercambiar_codigo(code: str, ctx: Context) -> str:
    """Intercambia el código de autorización por tokens de acceso."""
    http = ctx.request_context.lifespan_state["http"]
    credentials = load_credentials()
    
    if not credentials:
        return json.dumps({"error": "No hay credenciales. Ejecuta gmail_autenticar primero"})
    
    try:
        resp = await http.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"],
                "code": code,
                "redirect_uri": "http://localhost:8080/callback",
                "grant_type": "authorization_code"
            }
        )
        resp.raise_for_status()
        token = resp.json()
        
        # Guardar token
        token["expires_at"] = datetime.datetime.now().timestamp() + token["expires_in"]
        save_token(token)
        
        # Crear etiquetas
        await crear_etiquetas(http, token["access_token"])
        
        return json.dumps({
            "autenticado": True,
            "expires_in": token["expires_in"]
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── Arranque ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
