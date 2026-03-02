#!/usr/bin/env python3
"""
AlertHub - Gmail + LinkedIn + WhatsApp Notifications
Bot integrado que notifica por Telegram sobre:
- Emails importantes de Gmail (con enlaces directos)
- Notificaciones de LinkedIn
- WhatsApp (FUTURO: leer y resumir mensajes)
"""

import json
import os
import datetime
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

import httpx
import base64
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from telegram import Bot

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger("alert_hub")

# Shared config - use finbot's working .env
FINBOT_ENV = Path("/root/finbot_mcp/finbot_mcp/.env")

# ─── Integraciones Disponibles ───────────────────────────────────────────────
# Gmail: ✅ Activo
# LinkedIn: ⚠️ Requiere Playwright
# WhatsApp: 🔜 Pendiente (leer y resumir mensajes)

# Default values (can be overridden by FINBOT_ENV)
TELEGRAM_BOT_TOKEN = "8674886397:AAHDvxVXf1JsXuFX_2ndifpACq3WTpUxKlY"  # NotificenterBot
TELEGRAM_CHAT_ID = "930463010"
GOOGLE_SERVICE_ACCOUNT_JSON = ""
LINKEDIN_SESSION_FILE = ""

def load_config():
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GOOGLE_SERVICE_ACCOUNT_JSON, LINKEDIN_SESSION_FILE
    
    # Load from finbot's .env (has working values)
    if FINBOT_ENV.exists():
        content = FINBOT_ENV.read_text()
        
        # Find and extract the Google Service Account JSON
        start_marker = 'GOOGLE_SERVICE_ACCOUNT_JSON='
        start_idx = content.find(start_marker)
        
        if start_idx != -1:
            # Find the start of JSON (after =)
            json_start = start_idx + len(start_marker)
            # Find the end (next key, which is GOOGLE_SHEETS_ID)
            end_marker = '\nGOOGLE_SHEETS_ID='
            end_idx = content.find(end_marker, json_start)
            
            if end_idx != -1:
                raw_json = content[json_start:end_idx]
                logger.info(f"Raw JSON length: {len(raw_json)}")
                # Unescape \n to actual newlines and clean control chars
                GOOGLE_SERVICE_ACCOUNT_JSON = raw_json.replace('\n', '\n')
                logger.info(f"After replace length: {len(GOOGLE_SERVICE_ACCOUNT_JSON)}")
                # Remove invalid control characters except newlines and tabs
                GOOGLE_SERVICE_ACCOUNT_JSON = ''.join(
                    c for c in GOOGLE_SERVICE_ACCOUNT_JSON 
                    if c in '\n\r\t' or (ord(c) >= 32 and ord(c) != 127)
                )
                logger.info(f"After clean length: {len(GOOGLE_SERVICE_ACCOUNT_JSON)}")
        
        # Load other values
        for line in content.splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                val = val.strip()
                if key == "TELEGRAM_BOT_TOKEN" and val:
                    TELEGRAM_BOT_TOKEN = val
                elif key == "TELEGRAM_CHAT_ID" and val:
                    TELEGRAM_CHAT_ID = val
                elif key == "LINKEDIN_SESSION_FILE":
                    LINKEDIN_SESSION_FILE = val

load_config()

ETIQUETAS_AREAS = ["AREA_FINANZAS", "AREA_PERSONAL", "AREA_PROFESIONAL", "AREA_TECNICA", "AREA_APRENDIZAJE"]
ETIQUETAS_TIPO = ["TIPO_FACTURA", "TIPO_CONTRATO", "TIPO_LEGAL", "TIPO_NOTIFICACION", "TIPO_ACCESO", "TIPO_PROPUESTA", "TIPO_RENOVACION", "TIPO_REUNION", "TIPO_SUSCRIPCION"]
ETIQUETAS_ESTADO = ["ESTADO_PENDIENTE", "ESTADO_ESPERANDO", "ESTADO_RESUELTO"]

URGENTES = ["banco", "hacienda", "agencia tributaria", "deuda", "cobro", "jurídico", "abogado", "demanda", "sentencia", "multa", "seguro", "robo", "fraude", "alerta", "urgente", "importante", "card", "visa", "mastercard", "préstamo", "crédito"]

telegram_bot = None
if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    try:
        telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Error init Telegram: {e}")


async def send_telegram(message: str, parse_mode: str = "Markdown"):
    """Envía mensaje por Telegram"""
    if not telegram_bot or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram no configurado")
        return {"success": False, "error": "Telegram not configured"}
    
    try:
        await telegram_bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode=parse_mode
        )
        return {"success": True}
    except Exception as e:
        logger.error(f"Error sending Telegram: {e}")
        return {"success": False, "error": str(e)}


# OAuth2 token path for Gmail
GMAIL_TOKEN_PATH = Path("/root/gmail_mcp/token.json")

# Cache for access token
_gmail_access_token = {"token": None, "expires_at": 0}

async def get_gmail_token(http: httpx.AsyncClient) -> str:
    """Obtiene token de acceso para Gmail API usando OAuth2 refresh_token"""
    import time
    
    # Check if we have a valid cached token
    if _gmail_access_token["token"] and time.time() < _gmail_access_token["expires_at"] - 60:
        return _gmail_access_token["token"]
    
    # Load refresh token from gmail_mcp
    if not GMAIL_TOKEN_PATH.exists():
        raise Exception("No Gmail token found")
    
    token_data = json.loads(GMAIL_TOKEN_PATH.read_text())
    refresh_token = token_data.get("refresh_token")
    
    if not refresh_token:
        raise Exception("No refresh_token found")
    
    # Exchange refresh_token for new access_token
    token_url = "https://oauth2.googleapis.com/token"
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    
    # Make the refresh request
    resp = await http.post(
        token_url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
    )
    
    if resp.status_code != 200:
        raise Exception(f"Token refresh failed: {resp.text}")
    
    token_response = resp.json()
    new_access_token = token_response["access_token"]
    new_expires_at = time.time() + token_response.get("expires_in", 3600)
    
    # Update cache
    _gmail_access_token["token"] = new_access_token
    _gmail_access_token["expires_at"] = new_expires_at
    
    # Also update the stored token
    token_data["token"] = new_access_token
    token_data["expires_at"] = new_expires_at
    GMAIL_TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
    
    return new_access_token


async def check_gmail_important(http: httpx.AsyncClient, max_results: int = 10) -> Dict:
    """Busca emails importantes sin clasificar y retorna con enlaces"""
    
    try:
        token = await get_gmail_token(http)
    except Exception as e:
        return {"error": f"Failed to get Gmail token: {e}"}
    
    q = "is:unread"
    
    try:
        resp = await http.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers={"Authorization": f"Bearer {token}"},
            params={"maxResults": max_results, "q": q}
        )
        resp.raise_for_status()
    except Exception as e:
        return {"error": f"Gmail API error: {e}"}
    
    mensajes = resp.json().get("messages", [])
    emails = []
    
    for m in mensajes[:max_results]:
        try:
            msg_resp = await http.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{m['id']}",
                headers={"Authorization": f"Bearer {token}"},
                params={"format": "full"}
            )
            msg_resp.raise_for_status()
            msg = msg_resp.json()
            
            subject = ""
            sender = ""
            snippet = msg.get("snippet", "")
            
            for header in msg.get("payload", {}).get("headers", []):
                if header["name"].lower() == "subject":
                    subject = header["value"]
                if header["name"].lower() == "from":
                    sender = header["value"]
            
            urgente = any(p in (subject + sender + snippet).lower() for p in URGENTES)
            
            email_link = f"https://mail.google.com/mail/u/0/#inbox/{m['id']}"
            
            emails.append({
                "id": m["id"],
                "subject": subject[:100],
                "sender": sender[:100],
                "snippet": snippet[:150],
                "urgent": urgente,
                "link": email_link
            })
            
            if urgente:
                await send_telegram(
                    f"🚨 *EMAIL URGENTE*\n\n*De:* {sender}\n*Asunto:* {subject}\n[Ver email]({email_link})"
                )
        
        except Exception as e:
            logger.error(f"Error processing email {m['id']}: {e}")
    
    return {
        "emails": emails,
        "total": len(emails),
        "urgent_count": sum(1 for e in emails if e["urgent"])
    }


# LinkedIn config
LINKEDIN_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
LINKEDIN_VIEWPORT = {"width": 1366, "height": 768}

# Paths to check for LinkedIn session
LINKEDIN_SESSION_PATHS = [
    Path("/root/linkedin_mcp/session.json"),
    Path("/root/alert_hub/session.json"),
]

def get_linkedin_session():
    """Get LinkedIn session from either location"""
    for p in LINKEDIN_SESSION_PATHS:
        if p.exists():
            return p
    return None


async def check_linkedin_notifications(limit: int = 5) -> Dict:
    """Verifica notificaciones de LinkedIn usando Playwright"""
    session_path = get_linkedin_session()
    if not session_path:
        return {
            "status": "error",
            "message": "No LinkedIn session found. Please login first using linkedin_mcp."
        }
    
    try:
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=LINKEDIN_USER_AGENT,
            viewport=LINKEDIN_VIEWPORT
        )
        
        # Load session cookies
        try:
            cookies = json.loads(LINKEDIN_SESSION_FILE.read_text())
            await page.context.add_cookies(cookies)
        except Exception as e:
            await browser.close()
            await playwright.stop()
            return {"status": "error", "message": f"Failed to load session: {e}"}
        
        # Check login
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        if "login" in page.url.lower():
            await browser.close()
            await playwright.stop()
            return {"status": "error", "message": "LinkedIn session expired"}
        
        # Get notifications
        await page.goto("https://www.linkedin.com/notifications/", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        notifications = []
        try:
            items = await page.query_selector_all(".notification-item, .social-notifications__notification")
            for item in items[:limit]:
                try:
                    text = await item.inner_text()
                    notifications.append(text[:150])
                except:
                    pass
        except:
            pass
        
        await browser.close()
        await playwright.stop()
        
        return {
            "status": "ok",
            "notifications": notifications,
            "total": len(notifications)
        }
        
    except ImportError:
        return {
            "status": "error",
            "message": "Playwright not installed. Run: pip install playwright && playwright install chromium"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


async def send_daily_summary():
    """Envía resumen diario de ambos servicios"""
    async with httpx.AsyncClient(timeout=30.0) as http:
        gmail_result = await check_gmail_important(http, max_results=5)
        
        message = "📊 *Resumen Diario*\n\n"
        
        if "emails" in gmail_result:
            message += f"📧 *Gmail:* {gmail_result['total']} emails importantes\n"
            if gmail_result.get("urgent_count", 0) > 0:
                message += f"   🚨 {gmail_result['urgent_count']} urgentes\n"
        
        linkedin_result = await check_linkedin_notifications()
        if linkedin_result.get("status") == "pending_implementation":
            message += "\n🔗 *LinkedIn:* Pendiente implementar"
        
        await send_telegram(message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AlertHub starting...")
    yield
    logger.info("AlertHub stopping...")


app = FastAPI(title="AlertHub", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "running",
        "service": "unified_bot",
        "telegram_configured": bool(telegram_bot and TELEGRAM_BOT_TOKEN)
    }


@app.get("/gmail/check")
async def check_gmail(limit: int = 10):
    """Verifica emails importantes y retorna con enlaces"""
    async with httpx.AsyncClient(timeout=30.0) as http:
        result = await check_gmail_important(http, max_results=limit)
        return result


@app.get("/linkedin/check")
async def check_linkedin():
    """Verifica notificaciones de LinkedIn"""
    result = await check_linkedin_notifications()
    return result


@app.get("/whatsapp/check")
async def check_whatsapp():
    """🔜 FUTURO: Verifica mensajes de WhatsApp"""
    return {
        "status": "pending",
        "message": "WhatsApp integration coming soon",
        "planned_features": [
            "Leer mensajes nuevos",
            "Resumir conversaciones",
            "Notificar por Telegram"
        ]
    }


@app.post("/notify")
async def send_notification(message: str, urgent: bool = False):
    """Envía notificación manual por Telegram"""
    prefix = "🚨 " if urgent else "📢 "
    result = await send_telegram(prefix + message)
    return result


@app.post("/test")
async def test_all():
    """Testea todas las integraciones"""
    results = {}
    
    results["telegram"] = await send_telegram("✅ Unified Bot test - ¡Todo funcionando!")
    
    async with httpx.AsyncClient(timeout=30.0) as http:
        results["gmail"] = await check_gmail_important(http, max_results=3)
    
    results["linkedin"] = await check_linkedin_notifications()
    
    return results


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "31436"))
    host = os.environ.get("HOST", "0.0.0.0")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        log_level="info"
    )
