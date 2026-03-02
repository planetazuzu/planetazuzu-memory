#!/usr/bin/env python3
"""
linkedin_mcp — MCP Server para gestión de LinkedIn
Usa Playwright con comportamiento humano simulado.
"""

import json
import os
import random
import time
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Browser, Page, Playwright
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP, Context

import httpx

# ─── Configuración ────────────────────────────────────────────────────────────

SESSION_PATH = Path("/root/linkedin_mcp/session.json")
DAILY_LIMIT_PATH = Path("/root/linkedin_mcp/daily_limit.json")
MENSajes_PATH = Path("/root/linkedin_mcp/mensajes.json")
ACTIVITY_LOG = Path("/root/linkedin_mcp/activity.log")
TELEGRAM_BOT_TOKEN = "8764458493:AAGgNOXJq09YpZgoyO8sWb7Opi94jSNrv60"
TELEGRAM_CHAT_ID = "930463010"
GOOGLE_SHEETS_ID = "1w_tUSvjZ1lqjL-hihJw83XcsbXoBzeCbLr8X68B1_Fg"
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

# Configuración anti-detección
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
VIEWPORT = {"width": 1366, "height": 768}

# Límites
MAX_ACTIONS_PER_DAY = 50
ALLOWED_HOURS = (9, 20)  # 9:00 - 20:00

# ─── Helpers ────────────────────────────────────────────────────────────

def log_activity(action: str, details: str = ""):
    """Registra actividad en el log"""
    timestamp = datetime.datetime.now().isoformat()
    with open(ACTIVITY_LOG, "a") as f:
        f.write(f"[{timestamp}] {action}: {details}\n")

def get_daily_count() -> int:
    """Obtiene el contador de acciones diarias"""
    if DAILY_LIMIT_PATH.exists():
        data = json.loads(DAILY_LIMIT_PATH.read_text())
        fecha = data.get("fecha", "")
        hoy = datetime.date.today().isoformat()
        if fecha == hoy:
            return data.get("contador", 0)
    return 0

def increment_daily_count():
    """Incrementa el contador diario"""
    hoy = datetime.date.today().isoformat()
    if DAILY_LIMIT_PATH.exists():
        data = json.loads(DAILY_LIMIT_PATH.read_text())
    else:
        data = {"fecha": "", "contador": 0}
    
    if data.get("fecha", "") != hoy:
        data = {"fecha": hoy, "contador": 0}
    
    data["contador"] += 1
    DAILY_LIMIT_PATH.write_text(json.dumps(data, indent=2))
    return data["contador"]

def can_execute() -> bool:
    """Verifica si se puede ejecutar una acción"""
    # Verificar hora
    ahora = datetime.datetime.now().hour
    if ahora < ALLOWED_HOURS[0] or ahora >= ALLOWED_HOURS[1]:
        return False
    
    # Verificar límite diario
    if get_daily_count() >= MAX_ACTIONS_PER_DAY:
        return False
    
    return True

def human_delay(min_sec: float = 3, max_sec: float = 8):
    """Simula delay humano entre acciones"""
    time.sleep(random.uniform(min_sec, max_sec))

async def enviar_alerta_telegram(mensaje: str, foto: bytes = None):
    """Envía alerta por Telegram"""
    try:
        async with httpx.AsyncClient() as http:
            if foto:
                # Enviar con foto
                pass
            else:
                await http.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
                )
    except Exception as e:
        log_activity("ALERTA_TELEGRAM_ERROR", str(e))

# ─── Playwright Helpers ────────────────────────────────────────────────────

async def get_browser() -> Browser:
    """Inicia el navegador con configuración anti-detección"""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,  # Siempre visible para poder hacer login
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
        ]
    )
    return browser

async def load_session(page: Page) -> bool:
    """Carga cookies de sesión si existen"""
    if SESSION_PATH.exists():
        try:
            cookies = json.loads(SESSION_PATH.read_text())
            await page.context.add_cookies(cookies)
            return True
        except:
            return False
    return False

async def save_session(page: Page):
    """Guarda cookies de sesión"""
    cookies = await page.context.cookies()
    SESSION_PATH.write_text(json.dumps(cookies, indent=2))
    log_activity("SESSION_SAVED", "Cookies guardadas")

async def check_login(page: Page) -> bool:
    """Verifica si está logueado"""
    try:
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        human_delay(2, 4)
        # Buscar elemento que solo aparece cuando está logueado
        await page.wait_for_selector("#global-nav", timeout=5000)
        return True
    except:
        return False

async def tipo_humano(page: Page, texto: str):
    """Simula escritura humana tecla a tecla"""
    for char in texto:
        await page.keyboard.type(char, delay=random.randint(50, 150))
        if random.random() < 0.05:  # 5% de pausa extra
            time.sleep(random.uniform(0.1, 0.3))

# ─── Lifespan ────────────────────────────────────────────────────────────

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Inicializa el servidor"""
    log_activity("SERVER_START", "LinkedIn MCP iniciado")
    yield {}

mcp = FastMCP("linkedin_mcp", lifespan=app_lifespan)

# ─── Modelos ────────────────────────────────────────────────────────────

class ResponderMensajeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mensaje_id: str = Field(..., description="ID del mensaje a responder")
    texto: str = Field(..., description="Texto de la respuesta")

class ClasificarMensajeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mensaje_id: str = Field(..., description="ID del mensaje a clasificar")

class PublicarInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texto: str = Field(..., description="Texto de la publicación")

class ExtraerLeadsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    busqueda: str = Field(..., description="Búsqueda (ej: CTOs Madrid)")
    limite: int = Field(default=20, description="Límite de resultados", le=20)

class GuardarPerfilInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url_perfil: str = Field(..., description="URL del perfil de LinkedIn")

# ─── TOOLS ───────────────────────────────────────────────────────────────

@mcp.tool()
async def linkedin_guardar_sesion() -> str:
    """Abre Chromium para que hagas login manualmente y guarda las cookies.
    
    Ejecuta esto una vez. Abre LinkedIn, inicia sesión manualmente,
    y las cookies se guardarán automáticamente.
    """
    if not can_execute():
        return json.dumps({"error": "Outside allowed hours or daily limit reached"})
    
    log_activity("GUARDAR_SESION", "Iniciando navegador para login")
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page(
        user_agent=USER_AGENT,
        viewport=VIEWPORT
    )
    
    await page.goto("https://www.linkedin.com/login")
    human_delay(1, 2)
    
    # Esperar a que el usuario haga login
    await page.wait_for_selector("#global-nav", timeout=300000)  # 5 min timeout
    
    # Guardar cookies
    await save_session(page)
    
    await browser.close()
    await playwright.stop()
    
    increment_daily_count()
    
    return json.dumps({
        "guardado": True,
        "mensaje": "Sesión guardada correctamente. Ahora puedes usar las demás tools."
    })


@mcp.tool()
async def linkedin_leer_mensajes(limite: int = 10) -> str:
    """Lee los últimos mensajes no leídos de LinkedIn.
    
    Devuelve lista de mensajes con remitente, texto y fecha.
    Guarda automáticamente en mensajes.json.
    """
    if not can_execute():
        return json.dumps({"error": "Outside allowed hours or daily limit reached"})
    
    log_activity("LEER_MENSAJES", f"Limite: {limite}")
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=USER_AGENT,
            viewport=VIEWPORT
        )
        
        # Cargar sesión
        await load_session(page)
        
        # Verificar login
        if not await check_login(page):
            await browser.close()
            await playwright.stop()
            return json.dumps({"error": "No hay sesión activa. Ejecuta linkedin_guardar_sesion"})
        
        # Ir a mensajes
        await page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded")
        human_delay(3, 6)
        
        # Buscar mensajes no leídos
        mensajes = []
        
        # Intentar encontrar contenedores de mensajes
        try:
           conversations = await page.query_selector_all("[data-test-message-modal-content]")
            for conv in conversations[:limite]:
                try:
                    # Extraer info del mensaje
                    texto_elem = await conv.query_selector(".msg-form__message-text")
                    texto = await texto_elem.inner_text() if texto_elem else ""
                    
                    # Buscar remitente
                    sender_elem = await conv.query_selector(".msg-thread__participant-names")
                    remitente = await sender_elem.inner_text() if sender_elem else "Desconocido"
                    
                    mensajes.append({
                        "remitente": remitente.strip(),
                        "texto": texto.strip()[:200],
                        "fecha": datetime.datetime.now().isoformat()
                    })
                except:
                    pass
        except Exception as e:
            log_activity("ERROR_MENSAJES", str(e))
        
        # Guardar en archivo
        MENSajes_PATH.write_text(json.dumps(mensajes, indent=2, ensure_ascii=False))
        
        await browser.close()
        await playwright.stop()
        
        increment_daily_count()
        
        return json.dumps({
            "mensajes": mensajes,
            "total": len(mensajes)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        log_activity("ERROR_LEER_MENSAJES", str(e))
        return json.dumps({"error": str(e)})


@mcp.tool()
async def linkedin_clasificar_mensaje(params: ClasificarMensajeInput) -> str:
    """Clasifica un mensaje usando reglas predefinidas.
    
    Categorías: LEAD, COLABORACION, RECLUTADOR, SPAM, PERSONAL, CLIENTE
    """
    if not can_execute():
        return json.dumps({"error": "Outside allowed hours"})
    
    # Cargar mensajes
    if not MENSajes_PATH.exists():
        return json.dumps({"error": "No hay mensajes. Ejecuta linkedin_leer_mensajes primero"})
    
    mensajes = json.loads(MENSajes_PATH.read_text())
    
    # Buscar el mensaje
    mensaje = None
    for m in mensajes:
        if str(mensajes.index(m)) == params.mensaje_id:
            mensaje = m
            break
    
    if not mensaje:
        return json.dumps({"error": "Mensaje no encontrado"})
    
    # Clasificación simple basada en palabras clave
    texto = (mensaje.get("remitente", "") + " " + mensaje.get("texto", "")).lower()
    
    clasificacion = "PERSONAL"  # Por defecto
    
    if any(p in texto for p in ["cto", "tech", "developer", "programador", "software", "lead", "tech lead"]):
        clasificacion = "LEAD"
    elif any(p in texto for p in ["colaborar", "colaboration", "partner", "joint"]):
        clasificacion = "COLABORACION"
    elif any(p in texto for p in ["recruiter", "reclutador", "trabajo", "job", "empleo", "vacante"]):
        clasificacion = "RECLUTADOR"
    elif any(p in texto for p in ["spam", "promocion", "marketing", "click", "gana dinero"]):
        clasificacion = "SPAM"
    elif any(p in texto for p in ["cliente", "cliente", "servicio", "proyecto", "presupuesto"]):
        clasificacion = "CLIENTE"
    
    # Actualizar mensaje con clasificación
    mensaje["clasificacion"] = clasificacion
    MENSajes_PATH.write_text(json.dumps(mensajes, indent=2, ensure_ascii=False))
    
    # Alertar si es LEAD o CLIENTE
    if clasificacion in ["LEAD", "CLIENTE"]:
        await enviar_alerta_telegram(f"🔔 Nuevo {clasificacion}: {mensaje.get('remitente', 'Desconocido')}\n{mensaje.get('texto', '')[:100]}...")
    
    increment_daily_count()
    
    return json.dumps({
        "mensaje_id": params.mensaje_id,
        "clasificacion": clasificacion
    })


@mcp.tool()
async def linkedin_responder_mensaje(params: ResponderMensajeInput) -> str:
    """Responde a un mensaje con texto dado.
    
    Simula escritura humana (tecla a tecla).
    """
    if not can_execute():
        return json.dumps({"error": "Outside allowed hours or daily limit"})
    
    log_activity("RESPONDER_MENSAJE", params.mensaje_id)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=USER_AGENT,
            viewport=VIEWPORT
        )
        
        await load_session(page)
        
        if not await check_login(page):
            return json.dumps({"error": "No hay sesión activa"})
        
        # Ir al mensaje
        await page.goto(f"https://www.linkedin.com/messaging/thread/{params.mensaje_id}/", wait_until="domcontentloaded")
        human_delay(3, 5)
        
        # Encontrar input de respuesta
        await page.wait_for_selector(".msg-form__message-editor", timeout=10000)
        
        # Escribir respuesta lentamente
        await page.click(".msg-form__message-editor")
        await tipo_humano(page, params.texto)
        
        human_delay(1, 2)
        
        # Enviar (buscar botón de enviar)
        await page.keyboard.press("Enter")
        
        human_delay(2, 4)
        
        await browser.close()
        await playwright.stop()
        
        increment_daily_count()
        
        return json.dumps({"enviado": True, "mensaje_id": params.mensaje_id})
        
    except Exception as e:
        log_activity("ERROR_RESPONDER", str(e))
        return json.dumps({"error": str(e)})


@mcp.tool()
async def linkedin_ver_notificaciones() -> str:
    """Lee las últimas notificaciones de LinkedIn."""
    if not can_execute():
        return json.dumps({"error": "Outside allowed hours"})
    
    log_activity("VER_NOTIFICACIONES", "Inicio")
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=USER_AGENT,
            viewport=VIEWPORT
        )
        
        await load_session(page)
        
        if not await check_login(page):
            return json.dumps({"error": "No hay sesión"})
        
        await page.goto("https://www.linkedin.com/notifications/", wait_until="domcontentloaded")
        human_delay(3, 6)
        
        # Extraer notificaciones
        notificaciones = []
        items = await page.query_selector_all(".notification-item")
        
        for item in items[:15]:
            try:
                texto = await item.inner_text()
                notificaciones.append(texto[:100])
            except:
                pass
        
        await browser.close()
        await playwright.stop()
        
        increment_daily_count()
        
        return json.dumps({
            "notificaciones": notificaciones,
            "total": len(notificaciones)
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def linkedin_guardar_perfil(params: GuardarPerfilInput) -> str:
    """Guarda datos de un perfil en Google Sheets (hoja LinkedIn_Perfiles)."""
    if not can_execute():
        return json.dumps({"error": "Outside allowed hours"})
    
    log_activity("GUARDAR_PERFIL", params.url_perfil)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=USER_AGENT,
            viewport=VIEWPORT
        )
        
        await load_session(page)
        
        if not await check_login(page):
            return json.dumps({"error": "No hay sesión"})
        
        await page.goto(params.url_perfil, wait_until="domcontentloaded")
        human_delay(3, 6)
        
        # Extraer datos del perfil
        datos = {"url": params.url_perfil}
        
        try:
            nombre_elem = await page.query_selector(".pv-top-card__name")
            datos["nombre"] = await nombre_elem.inner_text() if nombre_elem else ""
        except:
            pass
        
        try:
            cargo_elem = await page.query_selector(".pv-top-card__headline")
            datos["cargo"] = await cargo_elem.inner_text() if cargo_elem else ""
        except:
            pass
        
        try:
            empresa_elem = await page.query_selector(".pv-top-card__company-name")
            datos["empresa"] = await empresa_elem.inner_text() if empresa_elem else ""
        except:
            pass
        
        await browser.close()
        await playwright.stop()
        
        # Guardar en Sheets
        if SERVICE_ACCOUNT_JSON:
            from google.oauth2 import service_account
            import google.auth.transport.requests
            
            creds_info = json.loads(SERVICE_ACCOUNT_JSON)
            creds = service_account.Credentials.from_service_account_info(
                creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            request = google.auth.transport.requests.Request()
            creds.refresh(request)
            
            async with httpx.AsyncClient() as http:
                # Intentar escribir, si no existe la hoja crearla
                url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEETS_ID}/values/LinkedIn_Perfiles!A1?valueInputOption=USER_ENTERED"
                filas = [[datos.get("nombre", ""), datos.get("cargo", ""), datos.get("empresa", ""), datos.get("url", "")]]
                resp = await http.put(url, headers={"Authorization": f"Bearer {creds.token}"}, json={"values": filas})
        
        increment_daily_count()
        
        return json.dumps({"guardado": True, "perfil": datos})
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def linkedin_publicar(params: PublicarInput) -> str:
    """Publica un texto en el feed de LinkedIn.
    
    Solo 1 publicación por día, solo entre 9:00-20:00.
    """
    if not can_execute():
        return json.dumps({"error": "Outside allowed hours or daily limit"})
    
    # Verificar si ya publicó hoy
    if DAILY_LIMIT_PATH.exists():
        data = json.loads(DAILY_LIMIT_PATH.read_text())
        if data.get("publicado_hoy", False):
            return json.dumps({"error": "Ya publicaste hoy. Máximo 1 publicación por día."})
    
    log_activity("PUBLICAR", "Inicio")
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=USER_AGENT,
            viewport=VIEWPORT
        )
        
        await load_session(page)
        
        if not await check_login(page):
            return json.dumps({"error": "No hay sesión"})
        
        # Ir al feed
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        human_delay(3, 5)
        
        # Click en botón de crear post
        await page.click(".feed-shared-create-button")
        human_delay(2, 4)
        
        # Escribir post
        await page.wait_for_selector(".feed-shared-editor__content")
        await page.click(".feed-shared-editor__content")
        await tipo_humano(page, params.texto)
        
        human_delay(1, 2)
        
        # Click en publicar
        await page.click(".feed-shared-editor__submit-button")
        
        human_delay(3, 5)
        
        await browser.close()
        await playwright.stop()
        
        # Marcar como publicado hoy
        if DAILY_LIMIT_PATH.exists():
            data = json.loads(DAILY_LIMIT_PATH.read_text())
        else:
            data = {"fecha": "", "contador": 0}
        data["publicado_hoy"] = True
        DAILY_LIMIT_PATH.write_text(json.dumps(data))
        
        increment_daily_count()
        
        return json.dumps({"publicado": True})
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def linkedin_extraer_leads(params: ExtraerLeadsInput) -> str:
    """Extrae perfiles de una búsqueda de LinkedIn y guarda en Sheets."""
    if not can_execute():
        return json.dumps({"error": "Outside allowed hours"})
    
    log_activity("EXTRAER_LEADS", f"Busqueda: {params.busqueda}")
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=USER_AGENT,
            viewport=VIEWPORT
        )
        
        await load_session(page)
        
        if not await check_login(page):
            return json.dumps({"error": "No hay sesión"})
        
        # Buscar
        busqueda_url = f"https://www.linkedin.com/search/results/people/?keywords={params.busqueda.replace(' ', '%20')}"
        await page.goto(busqueda_url, wait_until="domcontentloaded")
        human_delay(3, 6)
        
        # Extraer resultados
        resultados = []
        items = await page.query_selector_all(".reusable-search__result-container")[:params.limite]
        
        for item in items:
            try:
                nombre = ""
                cargo = ""
                url = ""
                
                nombre_elem = await item.query_selector(".entity-result__title-text")
                if nombre_elem:
                    nombre = await nombre_elem.inner_text()
                
                cargo_elem = await item.query_selector(".entity-result__primary-subtitle")
                if cargo_elem:
                    cargo = await cargo_elem.inner_text()
                
                link_elem = await item.query_selector("a.app-aware-link")
                if link_elem:
                    url = await link_elem.get_attribute("href")
                    url = url.split("?")[0] if url else ""
                
                if nombre:
                    resultados.append({
                        "nombre": nombre.strip(),
                        "cargo": cargo.strip() if cargo else "",
                        "url": url
                    })
            except:
                pass
        
        await browser.close()
        await playwright.stop()
        
        # Guardar en Sheets
        if SERVICE_ACCOUNT_JSON and resultados:
            from google.oauth2 import service_account
            import google.auth.transport.requests
            
            creds_info = json.loads(SERVICE_ACCOUNT_JSON)
            creds = service_account.Credentials.from_service_account_info(
                creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            request = google.auth.transport.requests.Request()
            creds.refresh(request)
            
            async with httpx.AsyncClient() as http:
                filas = [["Nombre", "Cargo", "URL"]]
                for r in resultados:
                    filas.append([r.get("nombre", ""), r.get("cargo", ""), r.get("url", "")])
                
                url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEETS_ID}/values/Leads!A1?valueInputOption=USER_ENTERED"
                await http.put(url, headers={"Authorization": f"Bearer {creds.token}"}, json={"values": filas})
        
        increment_daily_count()
        
        return json.dumps({
            "leads": resultados,
            "total": len(resultados)
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── Main ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
