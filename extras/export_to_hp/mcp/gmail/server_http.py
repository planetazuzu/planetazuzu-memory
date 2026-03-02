#!/usr/bin/env python3
"""
gmail_mcp — Servidor HTTP para gestión de Gmail
Versión HTTP independiente del MCP de Gmail.
"""

import json
import os
import datetime
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

import httpx
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger("gmail_mcp")

# ─── Configuración ────────────────────────────────────────────────────────────

TOKEN_PATH = Path("/root/gmail_mcp/token.json")
CREDENTIALS_PATH = Path("/root/gmail_mcp/credentials.json")
ENV_FILE = Path("/root/finbot_mcp/finbot_mcp/.env")

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
GOOGLE_SHEETS_ID = ""
SERVICE_ACCOUNT_JSON = ""

def load_env():
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GOOGLE_SHEETS_ID, SERVICE_ACCOUNT_JSON
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                if key == "TELEGRAM_BOT_TOKEN":
                    TELEGRAM_BOT_TOKEN = val
                elif key == "TELEGRAM_CHAT_ID":
                    TELEGRAM_CHAT_ID = val
                elif key == "GOOGLE_SHEETS_ID":
                    GOOGLE_SHEETS_ID = val
                elif key == "GOOGLE_SERVICE_ACCOUNT_JSON":
                    SERVICE_ACCOUNT_JSON = val

load_env()

# Etiquetas del sistema
ETIQUETAS_AREAS = ["AREA_FINANZAS", "AREA_PERSONAL", "AREA_PROFESIONAL", "AREA_TECNICA", "AREA_APRENDIZAJE"]
ETIQUETAS_TIPO = ["TIPO_FACTURA", "TIPO_CONTRATO", "TIPO_LEGAL", "TIPO_NOTIFICACION", "TIPO_ACCESO", "TIPO_PROPUESTA", "TIPO_RENOVACION", "TIPO_REUNION", "TIPO_SUSCRIPCION"]
ETIQUETAS_ESTADO = ["ESTADO_PENDIENTE", "ESTADO_ESPERANDO", "ESTADO_RESUELTO"]

URGENTES = ["banco", "hacienda", "agencia tributaria", "deuda", "cobro", "jurídico", "abogado", "demanda", "sentencia", "multa", "seguro", "robo", "fraude", "alerta", "urgente", "importante", "card", "visa", "mastercard", "préstamo", "crédito"]

http_client: httpx.AsyncClient = None

# ─── Modelos ────────────────────────────────────────────────────────────────

class ExecuteRequest(BaseModel):
    tool: str
    payload: dict = Field(default_factory=dict)

class ExecuteResponse(BaseModel):
    status: str
    result: Optional[dict] = None
    message: Optional[str] = None

class ClasificarCorreoInput(BaseModel):
    message_id: str

class ClasificarMasivoInput(BaseModel):
    limite: int = Field(default=1000, ge=1, le=5000)
    batch_size: int = Field(default=50, ge=1, le=100)

# ─── Autenticación ─────────────────────────────────────────────────────────

def load_credentials() -> Optional[Dict]:
    if CREDENTIALS_PATH.exists():
        return json.loads(CREDENTIALS_PATH.read_text())
    return None

def load_token() -> Optional[Dict]:
    if TOKEN_PATH.exists():
        return json.loads(TOKEN_PATH.read_text())
    return None

async def get_gmail_token(http: httpx.AsyncClient, credentials: Dict) -> str:
    token = load_token()
    if not token:
        raise ValueError("No hay token. Necesitas autenticarte primero.")
    
    expires_at = token.get("expires_at", 0)
    if datetime.datetime.now().timestamp() >= expires_at - 300:
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
        token_data = resp.json()
        token["token"] = token_data["access_token"]
        token["expires_at"] = datetime.datetime.now().timestamp() + token_data["expires_in"]
        TOKEN_PATH.write_text(json.dumps(token, indent=2))
    
    return token["token"]

async def obtener_id_etiquetas(http: httpx.AsyncClient, token: str) -> Dict[str, str]:
    resp = await http.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/labels",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    labels = resp.json().get("labels", {})
    return {l["name"]: l["id"] for l in labels}

async def ensure_labels(http: httpx.AsyncClient, token: str, ids_etiquetas: Dict[str, str]) -> Dict[str, str]:
    all_labels = ETIQUETAS_AREAS + ETIQUETAS_TIPO + ETIQUETAS_ESTADO
    for label in all_labels:
        if label not in ids_etiquetas:
            resp = await http.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/labels",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": label, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
            )
            if resp.status_code == 200:
                ids_etiquetas[label] = resp.json()["id"]
    return ids_etiquetas

async def send_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        async with httpx.AsyncClient() as http:
            await http.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
            )
    except Exception as e:
        logger.error(f"Error Telegram: {e}")

async def get_google_token() -> str:
    import google.auth.transport.requests
    from google.oauth2 import service_account
    service_info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = service_account.Credentials.from_service_account_info(
        service_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token

async def classify_email(subject: str, body: str, sender: str) -> dict:
    """Clasifica usando IA - Anthropic Claude"""
    prompt = f"""Clasifica este correo:

ÁREAS: {', '.join(ETIQUETAS_AREAS)}
TIPOS: {', '.join(ETIQUETAS_TIPO)}
ESTADOS: {', '.join(ETIQUETAS_ESTADO)}

De: {sender}
Asunto: {subject}
Cuerpo: {body[:500]}

Responde SOLO JSON: {{"area": "X", "tipo": "X", "estado": "X", "urgente": true/false}}"""
    
    try:
        from anthropic import Anthropic
        client = Anthropic()
        msg = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text
        for line in text.split('\n'):
            if '{' in line and '}' in line:
                start = line.find('{')
                end = line.rfind('}') + 1
                return json.loads(line[start:end])
    except Exception as e:
        logger.error(f"Error IA: {e}")
    
    return {"area": "AREA_PERSONAL", "tipo": "TIPO_NOTIFICACION", "estado": "ESTADO_PENDIENTE", "urgente": False}

def extract_invoice(body: str, sender: str) -> dict:
    data = {"emisor": sender, "importe": 0, "fecha": "", "concepto": "", "nif": ""}
    
    for pattern in [r'(\d+[.,]\d{2})\s*€', r'€\s*(\d+[.,]\d{2})', r'Total:\s*(\d+[.,]\d{2})']:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            data["importe"] = float(match.group(1).replace(',', '.'))
            break
    
    match = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})', body)
    if match:
        data["fecha"] = match.group(0)
    
    nif_match = re.search(r'[A-Z]{1,3}\d{6,8}[A-Z]', body, re.IGNORECASE)
    if nif_match:
        data["nif"] = nif_match.group(0)
    
    return data

async def append_sheets(data: List[List[str]], sheet_name: str):
    if not GOOGLE_SHEETS_ID:
        return
    token = await get_google_token()
    async with httpx.AsyncClient(timeout=30) as http:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEETS_ID}/values/{sheet_name}!A1:append?valueInputOption=USER_ENTERED"
        await http.post(url, headers=headers, json={"values": data})

# ─── TOOLS ─────────────────────────────────────────────────────────────────

async def tool_gmail_clasificar_correo(payload: dict, http: httpx.AsyncClient) -> dict:
    message_id = payload.get("message_id")
    if not message_id:
        raise HTTPException(status_code=400, detail="message_id requerido")
    
    credentials = load_credentials()
    if not credentials:
        return {"error": "No hay credenciales OAuth"}
    
    token = await get_gmail_token(http, credentials)
    ids_etiquetas = await obtener_id_etiquetas(http, token)
    ids_etiquetas = await ensure_labels(http, token, ids_etiquetas)
    
    resp = await http.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"format": "full"}
    )
    resp.raise_for_status()
    msg = resp.json()
    
    headers_dict = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    subject = headers_dict.get("Subject", "")
    sender = headers_dict.get("From", "")
    
    body = ""
    if msg["payload"].get("body", {}).get("data"):
        import base64
        body = base64.urlsafe_b64decode(msg["payload"]["body"]["data"]).decode("utf-8", errors="ignore")
    elif msg["payload"].get("parts"):
        for part in msg["payload"]["parts"]:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                import base64
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                break
    
    clasificacion = await classify_email(subject, body, sender)
    
    label_ids = []
    for key in ["area", "tipo", "estado"]:
        label_name = clasificacion.get(key, "").upper()
        if label_name and label_name in ids_etiquetas:
            label_ids.append(ids_etiquetas[label_name])
    
    if label_ids:
        await http.post(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify",
            headers={"Authorization": f"Bearer {token}"},
            json={"addLabelIds": label_ids}
        )
    
    return {"clasificado": True, "clasificacion": clasificacion, "message_id": message_id}

async def tool_gmail_clasificar_masivo(payload: dict, http: httpx.AsyncClient) -> dict:
    limite = payload.get("limite", 1000)
    batch_size = payload.get("batch_size", 50)
    
    credentials = load_credentials()
    if not credentials:
        return {"error": "No hay credenciales OAuth"}
    
    token = await get_gmail_token(http, credentials)
    ids_etiquetas = await obtener_id_etiquetas(http, token)
    ids_etiquetas = await ensure_labels(http, token, ids_etiquetas)
    
    await send_telegram("🔄 *Clasificación masiva iniciada*\nProcesando correos...")
    
    q = " ".join([f"-label:{l}" for l in ETIQUETAS_AREAS + ETIQUETAS_TIPO])
    resp = await http.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers={"Authorization": f"Bearer {token}"},
        params={"maxResults": min(limite, 2000), "q": q}
    )
    resp.raise_for_status()
    mensajes = resp.json().get("messages", [])
    
    total = len(mensajes)
    clasificados = 0
    errores = 0
    
    for i in range(0, len(mensajes), batch_size):
        batch = mensajes[i:i+batch_size]
        
        for m in batch:
            try:
                resp = await http.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{m['id']}",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"format": "full"}
                )
                msg = resp.json()
                
                headers_dict = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                subject = headers_dict.get("Subject", "")
                sender = headers_dict.get("From", "")
                
                body = ""
                if msg["payload"].get("body", {}).get("data"):
                    import base64
                    body = base64.urlsafe_b64decode(msg["payload"]["body"]["data"]).decode("utf-8", errors="ignore")
                
                clasificacion = await classify_email(subject, body, sender)
                
                label_ids = []
                for key in ["area", "tipo", "estado"]:
                    label_name = clasificacion.get(key, "").upper()
                    if label_name and label_name in ids_etiquetas:
                        label_ids.append(ids_etiquetas[label_name])
                
                if label_ids:
                    await http.post(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{m['id']}/modify",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"addLabelIds": label_ids}
                    )
                
                clasificados += 1
            except Exception as e:
                errores += 1
        
        await send_telegram(f"📊 Progreso: {min(i+batch_size, total)}/{total}")
    
    await send_telegram(f"✅ *Completado*\n• Total: {total}\n• Clasificados: {clasificados}\n• Errores: {errores}")
    
    return {"total": total, "clasificados": clasificados, "errores": errores}

async def tool_gmail_monitorizar_nuevos(payload: dict, http: httpx.AsyncClient) -> dict:
    credentials = load_credentials()
    if not credentials:
        return {"error": "No hay credenciales OAuth"}
    
    token = await get_gmail_token(http, credentials)
    ids_etiquetas = await obtener_id_etiquetas(http, token)
    
    resp = await http.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers={"Authorization": f"Bearer {token}"},
        params={"maxResults": 30, "q": "is:unread"}
    )
    mensajes = resp.json().get("messages", [])
    
    nuevos = 0
    urgentes = []
    
    for m in mensajes[:20]:
        try:
            resp = await http.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{m['id']}",
                headers={"Authorization": f"Bearer {token}"},
                params={"format": "full"}
            )
            msg = resp.json()
            
            headers_dict = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            subject = headers_dict.get("Subject", "")
            sender = headers_dict.get("From", "")
            
            body = ""
            if msg["payload"].get("body", {}).get("data"):
                import base64
                body = base64.urlsafe_b64decode(msg["payload"]["body"]["data"]).decode("utf-8", errors="ignore")
            
            clasificacion = await classify_email(subject, body, sender)
            
            text_lower = (subject + body).lower()
            if any(kw in text_lower for kw in URGENTES):
                clasificacion["urgente"] = True
            
            label_ids = []
            for key in ["area", "tipo", "estado"]:
                label_name = clasificacion.get(key, "").upper()
                if label_name and label_name in ids_etiquetas:
                    label_ids.append(ids_etiquetas[label_name])
            
            if label_ids:
                await http.post(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{m['id']}/modify",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"addLabelIds": label_ids, "removeLabelIds": ["UNREAD"]}
                )
            
            nuevos += 1
            if clasificacion.get("urgente"):
                urgentes.append({"subject": subject, "sender": sender})
                
        except Exception as e:
            logger.error(f"Error: {e}")
    
    if urgentes:
        msg = "🚨 *Correos urgentes:*\n\n"
        for u in urgentes[:5]:
            msg += f"• {u['subject'][:50]}\n"
        await send_telegram(msg)
    
    return {"procesados": nuevos, "urgentes": len(urgentes)}

async def tool_gmail_extraer_factura(payload: dict, http: httpx.AsyncClient) -> dict:
    credentials = load_credentials()
    if not credentials:
        return {"error": "No hay credenciales OAuth"}
    
    token = await get_gmail_token(http, credentials)
    ids_etiquetas = await obtener_id_etiquetas(http, token)
    
    resp = await http.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers={"Authorization": f"Bearer {token}"},
        params={"maxResults": 50, "q": "label:TIPO_FACTURA -label:PROCESADA"}
    )
    mensajes = resp.json().get("messages", [])
    
    extraidas = []
    
    for m in mensajes:
        try:
            resp = await http.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{m['id']}",
                headers={"Authorization": f"Bearer {token}"},
                params={"format": "full"}
            )
            msg = resp.json()
            
            headers_dict = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            subject = headers_dict.get("Subject", "")
            sender = headers_dict.get("From", "")
            
            body = ""
            if msg["payload"].get("body", {}).get("data"):
                import base64
                body = base64.urlsafe_b64decode(msg["payload"]["body"]["data"]).decode("utf-8", errors="ignore")
            
            factura = extract_invoice(body, sender)
            factura["asunto"] = subject
            extraidas.append(factura)
            
            if "PROCESADA" in ids_etiquetas:
                await http.post(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{m['id']}/modify",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"addLabelIds": [ids_etiquetas["PROCESADA"]]}
                )
        except Exception as e:
            logger.error(f"Error: {e}")
    
    if extraidas and GOOGLE_SHEETS_ID:
        filas = [["Fecha", "Emisor", "NIF", "Importe", "Concepto", "Asunto"]]
        for f in extraidas:
            filas.append([f.get("fecha", ""), f.get("emisor", ""), f.get("nif", ""), str(f.get("importe", 0)), f.get("concepto", ""), f.get("asunto", "")[:50]])
        await append_sheets(filas, "Facturas")
    
    return {"extraidas": len(extraidas), "facturas": extraidas}

async def tool_gmail_resumen_matutino(payload: dict, http: httpx.AsyncClient) -> dict:
    credentials = load_credentials()
    if not credentials:
        return {"error": "No hay credenciales OAuth"}
    
    token = await get_gmail_token(http, credentials)
    
    areas_count = {}
    for area in ETIQUETAS_AREAS:
        resp = await http.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers={"Authorization": f"Bearer {token}"},
            params={"maxResults": 1, "q": f"label:{area} label:ESTADO_PENDIENTE"}
        )
        if resp.status_code == 200:
            result = resp.json()
            areas_count[area] = result.get("resultSizeEstimate", 0)
    
    msg = "📧 *Resumen Matutino*\n\n*Por Área:*\n"
    for area, count in sorted(areas_count.items(), key=lambda x: -x[1]):
        if count > 0:
            msg += f"  📁 {area}: {count}\n"
    
    total = sum(areas_count.values())
    msg += f"\n📊 *Total: {total}*"
    
    await send_telegram(msg)
    
    return {"total": total, "por_area": areas_count}

TOOL_HANDLERS = {
    "gmail_clasificar_correo": tool_gmail_clasificar_correo,
    "gmail_clasificar_masivo": tool_gmail_clasificar_masivo,
    "gmail_monitorizar_nuevos": tool_gmail_monitorizar_nuevos,
    "gmail_extraer_factura": tool_gmail_extraer_factura,
    "gmail_resumen_matutino": tool_gmail_resumen_matutino,
}

# ─── FastAPI ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    logger.info("=" * 50)
    logger.info("Gmail MCP HTTP Server starting...")
    
    http_client = httpx.AsyncClient(timeout=60.0)
    
    logger.info("✓ Server ready")
    logger.info("Available tools: " + ", ".join(TOOL_HANDLERS.keys()))
    
    yield
    await http_client.aclose()
    logger.info("Server shutdown")

app = FastAPI(
    title="Gmail MCP Server",
    description="Servidor HTTP para gestión de Gmail",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health():
    return {"status": "running"}

@app.post("/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest):
    logger.info(f"Executing: {request.tool}")
    
    handler = TOOL_HANDLERS.get(request.tool)
    if not handler:
        return ExecuteResponse(status="error", message=f"Tool '{request.tool}' no encontrada")
    
    try:
        result = await handler(request.payload, http_client)
        return ExecuteResponse(status="ok", result=result)
    except Exception as e:
        logger.error(f"Error: {e}")
        return ExecuteResponse(status="error", message=str(e))

@app.get("/auth/status")
async def auth_status():
    has_credentials = CREDENTIALS_PATH.exists()
    has_token = TOKEN_PATH.exists()
    return {"credentials": has_credentials, "token": has_token}

@app.get("/auth/url")
async def get_auth_url():
    """Genera URL de autorización OAuth2"""
    if not CREDENTIALS_PATH.exists():
        return JSONResponse({"status": "error", "message": "credentials.json no encontrado"}, status_code=400)
    
    import secrets
    state = secrets.token_urlsafe(16)
    
    credentials = json.loads(CREDENTIALS_PATH.read_text())
    client_id = credentials["client_id"]
    redirect_uri = "http://localhost:31435/auth/callback"
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.labels&"
        f"access_type=offline&"
        f"state={state}"
    )
    
    return {"status": "ok", "result": {"auth_url": auth_url, "state": state, "instrucciones": "Copia la URL, autoriza, y llama /auth/token con el código"}}

@app.get("/auth/callback")
async def auth_callback(code: str, state: str = ""):
    """Callback de OAuth2"""
    try:
        credentials = json.loads(CREDENTIALS_PATH.read_text())
        
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": credentials["client_id"],
                    "client_secret": credentials["client_secret"],
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": "http://localhost:31435/auth/callback"
                }
            )
            resp.raise_for_status()
            token_data = resp.json()
            
            token = {
                "token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_at": datetime.datetime.now().timestamp() + token_data.get("expires_in", 3600)
            }
            
            TOKEN_PATH.write_text(json.dumps(token, indent=2))
            
        return {"status": "ok", "message": "Token guardado correctamente"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/auth/token")
async def exchange_token(code: str):
    """Intercambia código por token"""
    try:
        credentials = json.loads(CREDENTIALS_PATH.read_text())
        
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": credentials["client_id"],
                    "client_secret": credentials["client_secret"],
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": "http://localhost:31435/auth/callback"
                }
            )
            resp.raise_for_status()
            token_data = resp.json()
            
            token = {
                "token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_at": datetime.datetime.now().timestamp() + token_data.get("expires_in", 3600)
            }
            
            TOKEN_PATH.write_text(json.dumps(token, indent=2))
            
        return {"status": "ok", "message": "Token guardado"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "31435"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
