#!/usr/bin/env python3
"""
cronjobs/linkedin_alertas.py - Tareas programadas para LinkedIn MCP
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import asyncio
import httpx
import datetime
from google.oauth2 import service_account
import google.auth.transport.requests

# Paths
SESSION_PATH = Path("/root/linkedin_mcp/session.json")
DAILY_LIMIT_PATH = Path("/root/linkedin_mcp/daily_limit.json")
MENSajes_PATH = Path("/root/linkedin_mcp/mensajes.json")
ACTIVITY_LOG = Path("/root/linkedin_mcp/activity.log")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GOOGLE_SHEETS_ID = "1w_tUSvjZ1lqjL-hihJw83XcsbXoBzeCbLr8X68B1_Fg"
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

# Config
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"
MAX_ACTIONS = 50
ALLOWED_HOURS = (9, 20)

def log_activity(action, details=""):
    with open(ACTIVITY_LOG, "a") as f:
        f.write(f"[{datetime.datetime.now().isoformat()}] {action}: {details}\n")

def can_execute():
    ahora = datetime.datetime.now().hour
    if ahora < ALLOWED_HOURS[0] or ahora >= ALLOWED_HOURS[1]:
        return False
    if DAILY_LIMIT_PATH.exists():
        data = json.loads(DAILY_LIMIT_PATH.read_text())
        if data.get("fecha", "") == datetime.date.today().isoformat():
            if data.get("contador", 0) >= MAX_ACTIONS:
                return False
    return True

def increment_count():
    hoy = datetime.date.today().isoformat()
    data = {"fecha": hoy, "contador": 0}
    if DAILY_LIMIT_PATH.exists():
        data = json.loads(DAILY_LIMIT_PATH.read_text())
    if data.get("fecha", "") != hoy:
        data = {"fecha": hoy, "contador": 0, "publicado_hoy": False}
    data["contador"] = data.get("contador", 0) + 1
    DAILY_LIMIT_PATH.write_text(json.dumps(data))

async def telegram_send(msg):
    try:
        async with httpx.AsyncClient() as http:
            await http.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
            )
    except:
        pass

async def tarea_leer_y_clasificar():
    """Lee mensajes, clasifica nuevos y alerta si hay LEAD/CLIENTE"""
    if not can_execute():
        print("Outside hours or limit")
        return
    
    log_activity("CRON_LEER_MENSAJES", "Inicio")
    
    from playwright.async_api import async_playwright
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=USER_AGENT)
        
        # Cargar cookies
        if SESSION_PATH.exists():
            cookies = json.loads(SESSION_PATH.read_text())
            await page.context.add_cookies(cookies)
        
        await page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(3, 6))
        
        # Leer mensajes
        mensajes = []
        # ... (simplificado para cron)
        
        # Clasificar y alertar
        for m in mensajes:
            texto = m.get("texto", "").lower()
            if any(p in texto for p in ["cto", "tech", "lead"]):
                await telegram_send(f"🔔 LEAD detectado: {m.get('remitente', '')}")
            elif any(p in texto for p in ["cliente", "proyecto"]):
                await telegram_send(f"🔔 CLIENTE detectado: {m.get('remitente', '')}")
        
        await browser.close()
        await playwright.stop()
        
        increment_count()
        print("OK")
        
    except Exception as e:
        log_activity("ERROR_CRON", str(e))

async def tarea_resumen_diario():
    """Resumen diario de notificaciones y mensajes"""
    if not can_execute():
        return
    
    msg = "📊 *LinkedIn - Resumen Diario*\n\n"
    msg += "Notificaciones: X pendientes\n"
    msg += "Mensajes: X nuevos\n"
    msg += "Leads: X\n"
    
    await telegram_send(msg)
    log_activity("CRON_RESUMEN", "Enviado")

TAREAS = {
    "leer_clasificar": tarea_leer_y_clasificar,
    "resumen": tarea_resumen_diario,
}

if __name__ == "__main__":
    import random
    if len(sys.argv) < 2 or sys.argv[1] not in TAREAS:
        print(f"Uso: python linkedin_alertas.py [{' | '.join(TAREAS.keys())}]")
    else:
        asyncio.run(TAREAS[sys.argv[1]]())
