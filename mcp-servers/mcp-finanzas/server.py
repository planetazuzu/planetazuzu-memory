"""
Finanzas MCP - Servidor HTTP Independiente
Expone las herramientas del MCP de finanzas via HTTP.
No depende de OpenCode, funciona como servicio autónomo.
"""

import os
import sys
import json
import datetime
import logging
from pathlib import Path
from typing import Optional, Any, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import httpx

# Cargar .env primero
env_path = Path(__file__).parent.parent / "finbot_mcp" / "finbot_mcp" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            if key not in os.environ:
                os.environ[key] = val

# Añadir el path de finbot_mcp para importar las funciones helper
finbot_mcp_path = Path(__file__).parent.parent / "finbot_mcp" / "finbot_mcp"
sys.path.insert(0, str(finbot_mcp_path))

import importlib.util
finbot_server_spec = importlib.util.spec_from_file_location("finbot_server", finbot_mcp_path / "server.py")
finbot_server = importlib.util.module_from_spec(finbot_server_spec)
finbot_server_spec.loader.exec_module(finbot_server)

_cargar_finanzas = finbot_server._cargar_finanzas
_guardar_finanzas = finbot_server._guardar_finanzas
_gastos_mes = finbot_server._gastos_mes
_verificar_presupuesto = finbot_server._verificar_presupuesto
_enviar_telegram = finbot_server._enviar_telegram
_google_token = finbot_server._google_token
FINANZAS_JSON = finbot_server.FINANZAS_JSON
TELEGRAM_BOT_TOKEN = finbot_server.TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID = finbot_server.TELEGRAM_CHAT_ID
GOOGLE_SHEETS_ID = finbot_server.GOOGLE_SHEETS_ID
GOOGLE_CALENDAR_ID = finbot_server.GOOGLE_CALENDAR_ID
RegistrarGastoInput = finbot_server.RegistrarGastoInput
RegistrarIngresoInput = finbot_server.RegistrarIngresoInput
ResumenMesInput = finbot_server.ResumenMesInput
ProximosPagosInput = finbot_server.ProximosPagosInput
AlertaTelegramInput = finbot_server.AlertaTelegramInput
SyncSheetsInput = finbot_server.SyncSheetsInput
CrearEventoCalendarInput = finbot_server.CrearEventoCalendarInput

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger("finanzas_mcp")


# ─── Modelos de Request/Response ────────────────────────────────────────────────

class ExecuteRequest(BaseModel):
    tool: str = Field(..., description="Nombre de la herramienta a ejecutar")
    payload: dict = Field(default_factory=dict, description="Parámetros de la herramienta")


class ExecuteResponse(BaseModel):
    status: str
    result: Optional[dict] = None
    message: Optional[str] = None


# ─── Herramientas (Tools) ────────────────────────────────────────────────────────

async def tool_finanzas_registrar_gasto(payload: dict, http_client: httpx.AsyncClient) -> dict:
    """Registra un nuevo gasto"""
    from server import RegistrarGastoInput
    
    try:
        params = RegistrarGastoInput(
            descripcion=payload["descripcion"],
            importe=float(payload["importe"]),
            categoria=payload["categoria"],
            fecha=payload.get("fecha")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parámetros inválidos: {e}")
    
    finanzas = _cargar_finanzas()
    fecha = params.fecha or datetime.date.today().isoformat()
    fecha_obj = datetime.date.fromisoformat(fecha)

    movimiento = {
        "fecha": fecha,
        "mes": fecha_obj.strftime("%B"),
        "descripcion": params.descripcion.upper(),
        "importe": -abs(params.importe),
        "tipo": "Gasto",
        "categoria": params.categoria
    }
    finanzas["movimientos"].append(movimiento)
    _guardar_finanzas(finanzas)

    gastos_mes = _gastos_mes(finanzas, fecha_obj.year, fecha_obj.month)
    total_cat = gastos_mes.get(params.categoria, 0)
    alerta = _verificar_presupuesto(finanzas, params.categoria, total_cat)

    return {
        "registrado": True,
        "movimiento": movimiento,
        "presupuesto_categoria": {
            "categoria": params.categoria,
            "total_mes": round(total_cat, 2),
            "limite": finanzas.get("presupuesto_mensual", {}).get("categorias", {}).get(params.categoria, {}).get("limite", 0)
        },
        "alerta": alerta
    }


async def tool_finanzas_registrar_ingreso(payload: dict, http_client: httpx.AsyncClient) -> dict:
    """Registra un nuevo ingreso"""
    from server import RegistrarIngresoInput
    
    try:
        params = RegistrarIngresoInput(
            descripcion=payload["descripcion"],
            importe=float(payload["importe"]),
            categoria=payload.get("categoria", "Ingreso"),
            fecha=payload.get("fecha")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parámetros inválidos: {e}")
    
    finanzas = _cargar_finanzas()
    fecha = params.fecha or datetime.date.today().isoformat()
    fecha_obj = datetime.date.fromisoformat(fecha)

    movimiento = {
        "fecha": fecha,
        "mes": fecha_obj.strftime("%B"),
        "descripcion": params.descripcion.upper(),
        "importe": abs(params.importe),
        "tipo": "Ingreso",
        "categoria": params.categoria
    }
    finanzas["movimientos"].append(movimiento)
    _guardar_finanzas(finanzas)

    ingresos_mes = sum(
        m["importe"] for m in finanzas["movimientos"]
        if m["tipo"] == "Ingreso"
        and datetime.date.fromisoformat(m["fecha"]).month == fecha_obj.month
        and datetime.date.fromisoformat(m["fecha"]).year == fecha_obj.year
    )

    return {
        "registrado": True,
        "movimiento": movimiento,
        "ingresos_totales_mes": round(ingresos_mes, 2)
    }


async def tool_finanzas_resumen_mes(payload: dict, http_client: httpx.AsyncClient) -> dict:
    """Genera resumen del mes"""
    from server import ResumenMesInput
    
    try:
        params = ResumenMesInput(
            año=payload.get("año"),
            mes=payload.get("mes")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parámetros inválidos: {e}")
    
    finanzas = _cargar_finanzas()
    hoy = datetime.date.today()
    año = params.año or hoy.year
    mes = params.mes or hoy.month

    ingresos = sum(
        m["importe"] for m in finanzas["movimientos"]
        if m["tipo"] == "Ingreso"
        and datetime.date.fromisoformat(m["fecha"]).month == mes
        and datetime.date.fromisoformat(m["fecha"]).year == año
    )
    gastos_cat = _gastos_mes(finanzas, año, mes)
    total_gastos = sum(gastos_cat.values())

    presupuesto = finanzas.get("presupuesto_mensual", {}).get("categorias", {})
    categorias_detalle = []
    alertas = []
    for cat, total in sorted(gastos_cat.items(), key=lambda x: -x[1]):
        limite = presupuesto.get(cat, {}).get("limite", 0)
        pct = (total / limite * 100) if limite > 0 else None
        alerta = _verificar_presupuesto(finanzas, cat, total)
        if alerta:
            alertas.append(alerta)
        categorias_detalle.append({
            "categoria": cat,
            "total": round(total, 2),
            "limite": limite,
            "pct_usado": round(pct, 1) if pct is not None else None
        })

    return {
        "periodo": f"{año}-{mes:02d}",
        "ingresos": round(ingresos, 2),
        "gastos_variables": round(total_gastos, 2),
        "balance_variable": round(ingresos - total_gastos, 2),
        "compromisos_fijos_estimados": finanzas["perfil_financiero"]["compromisos_fijos_mensuales"],
        "categorias": categorias_detalle,
        "alertas": alertas
    }


async def tool_finanzas_proximos_pagos(payload: dict, http_client: httpx.AsyncClient) -> dict:
    """Lista los compromisos fijos próximos"""
    from server import ProximosPagosInput
    
    try:
        params = ProximosPagosInput(dias=payload.get("dias", 7))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parámetros inválidos: {e}")
    
    finanzas = _cargar_finanzas()
    hoy = datetime.date.today()
    proximos = []

    for c in finanzas.get("compromisos_fijos", []):
        if not c.get("activo", True):
            continue
        dia = c.get("dia_cobro", 0)
        if not dia:
            continue
        try:
            fecha_pago = hoy.replace(day=dia)
            if fecha_pago < hoy:
                next_m = (hoy.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
                fecha_pago = next_m.replace(day=min(dia, 28))
            dias_restantes = (fecha_pago - hoy).days
            if 0 <= dias_restantes <= params.dias:
                proximos.append({
                    "nombre": c["nombre"],
                    "categoria": c.get("categoria", ""),
                    "importe": c["importe_mensual"],
                    "fecha": fecha_pago.isoformat(),
                    "dias_restantes": dias_restantes,
                    "alerta": c.get("alerta", "")
                })
        except ValueError:
            pass

    proximos.sort(key=lambda x: x["dias_restantes"])
    total = sum(abs(p["importe"]) for p in proximos)

    return {
        "desde": hoy.isoformat(),
        "hasta": (hoy + datetime.timedelta(days=params.dias)).isoformat(),
        "pagos": proximos,
        "total_comprometido": round(total, 2)
    }


async def tool_finanzas_estado_deudas(http_client: httpx.AsyncClient) -> dict:
    """Devuelve el estado de deudas"""
    finanzas = _cargar_finanzas()
    deudas = []
    total = 0.0

    for c in finanzas.get("compromisos_fijos", []):
        saldo = c.get("saldo_pendiente_feb25", 0)
        if saldo and saldo > 0:
            deudas.append({
                "nombre": c["nombre"],
                "categoria": c.get("categoria", ""),
                "saldo_pendiente": saldo,
                "cuota_mensual": abs(c.get("importe_mensual", 0)),
                "alerta": c.get("alerta", "")
            })
            total += saldo

    deudas.sort(key=lambda x: -x["saldo_pendiente"])
    return {
        "deudas": deudas,
        "total_deuda": round(total, 2),
        "perfil": finanzas["perfil_financiero"]["situacion"]
    }


async def tool_telegram_enviar_mensaje(payload: dict, http_client: httpx.AsyncClient) -> dict:
    """Envía mensaje por Telegram"""
    from server import AlertaTelegramInput
    
    try:
        params = AlertaTelegramInput(mensaje=payload["mensaje"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parámetros inválidos: {e}")
    
    ok = await _enviar_telegram(http_client, params.mensaje)
    return {"enviado": ok, "chars": len(params.mensaje)}


async def tool_telegram_enviar_resumen_semanal(http_client: httpx.AsyncClient) -> dict:
    """Envía resumen semanal por Telegram"""
    finanzas = _cargar_finanzas()
    hoy = datetime.date.today()

    hace_7 = hoy - datetime.timedelta(days=7)
    gastos_semana: Dict[str, float] = {}
    for m in finanzas.get("movimientos", []):
        fecha = datetime.date.fromisoformat(m["fecha"])
        if m["tipo"] == "Gasto" and hace_7 <= fecha <= hoy:
            cat = m.get("categoria", "Otros")
            gastos_semana[cat] = gastos_semana.get(cat, 0) + abs(m["importe"])

    total_semana = sum(gastos_semana.values())

    gastos_mes = _gastos_mes(finanzas, hoy.year, hoy.month)
    alertas = [
        _verificar_presupuesto(finanzas, cat, total)
        for cat, total in gastos_mes.items()
        if _verificar_presupuesto(finanzas, cat, total)
    ]

    proximos_raw = await tool_finanzas_proximos_pagos({"dias": 7}, http_client)
    pagos_str = "\n".join(
        f"  📌 {p['fecha'][8:10]}/{p['fecha'][5:7]} — {p['nombre']}: {abs(p['importe']):.2f}€"
        for p in proximos_raw["pagos"]
    ) or "  ✅ Sin pagos esta semana"

    lineas_gastos = "\n".join(
        f"  • {cat}: {total:.2f}€"
        for cat, total in sorted(gastos_semana.items(), key=lambda x: -x[1])
    ) or "  Sin gastos registrados"

    alertas_str = "\n".join(f"  {a}" for a in alertas) if alertas else "  ✅ Todo dentro del presupuesto"

    mensaje = f"""📊 *Resumen semanal — {hoy.strftime('%d/%m/%Y')}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💸 *Gastos últimos 7 días: {total_semana:.2f}€*
{lineas_gastos}

📅 *Próximos pagos:*
{pagos_str}

🔔 *Alertas presupuesto:*
{alertas_str}

_Situación: {finanzas['perfil_financiero']['situacion']} | Déficit estimado: {abs(finanzas['perfil_financiero']['deficit_mensual_estimado']):.0f}€/mes_"""

    ok = await _enviar_telegram(http_client, mensaje)
    return {"enviado": ok, "mensaje_preview": mensaje[:200]}


async def tool_sheets_sync_movimientos(payload: dict, http_client: httpx.AsyncClient) -> dict:
    """Sincroniza movimientos con Google Sheets"""
    from server import SyncSheetsInput
    
    try:
        params = SyncSheetsInput(
            mes=payload.get("mes"),
            año=payload.get("año")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parámetros inválidos: {e}")
    
    finanzas = _cargar_finanzas()
    hoy = datetime.date.today()
    mes = params.mes or hoy.month
    año = params.año or hoy.year

    try:
        token = await _google_token(http_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error autenticando con Google: {e}")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    sheet_id = GOOGLE_SHEETS_ID

    movs = [
        m for m in finanzas.get("movimientos", [])
        if datetime.date.fromisoformat(m["fecha"]).month == mes
        and datetime.date.fromisoformat(m["fecha"]).year == año
    ]
    movs.sort(key=lambda x: x["fecha"])

    filas = [["Fecha", "Descripción", "Importe", "Tipo", "Categoría"]]
    for m in movs:
        filas.append([m["fecha"], m["descripcion"], m["importe"], m["tipo"], m.get("categoria", "")])

    rango = f"Movimientos!A1"
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{rango}?valueInputOption=USER_ENTERED"
    
    try:
        resp = await http_client.put(url, headers=headers, json={"values": filas})
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sincronizando Sheets: {e}")

    sheets_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    return {
        "sincronizado": True,
        "filas_escritas": len(filas) - 1,
        "periodo": f"{año}-{mes:02d}",
        "url": sheets_url
    }


async def tool_calendar_crear_evento_pago(payload: dict, http_client: httpx.AsyncClient) -> dict:
    """Crea evento en Google Calendar"""
    from server import CrearEventoCalendarInput
    
    try:
        params = CrearEventoCalendarInput(
            titulo=payload["titulo"],
            fecha=payload["fecha"],
            importe=payload.get("importe"),
            descripcion=payload.get("descripcion")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parámetros inválidos: {e}")
    
    try:
        token = await _google_token(http_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error autenticando con Google: {e}")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    desc_parts = []
    if params.importe:
        desc_parts.append(f"Importe: {params.importe:.2f}€")
    if params.descripcion:
        desc_parts.append(params.descripcion)
    desc_parts.append("Creado por FinBot 🤖")

    evento = {
        "summary": f"💳 {params.titulo}",
        "description": "\n".join(desc_parts),
        "start": {"date": params.fecha},
        "end": {"date": params.fecha},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 1440},
                {"method": "popup", "minutes": 10080},
            ]
        },
        "colorId": "11"
    }

    url = f"https://www.googleapis.com/calendar/v3/calendars/{GOOGLE_CALENDAR_ID}/events"
    
    try:
        resp = await http_client.post(url, headers=headers, json=evento)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando evento: {e}")

    return {
        "creado": True,
        "evento_id": data.get("id"),
        "titulo": data.get("summary"),
        "fecha": params.fecha,
        "link": data.get("htmlLink")
    }


async def tool_calendar_sincronizar_compromisos(payload: dict, http_client: httpx.AsyncClient) -> dict:
    """Sincroniza compromisos fijos con Google Calendar"""
    finanzas = _cargar_finanzas()
    hoy = datetime.date.today()
    
    if hoy.month == 12:
        año_target, mes_target = hoy.year + 1, 1
    else:
        año_target, mes_target = hoy.year, hoy.month + 1

    creados = []
    errores = []

    for c in finanzas.get("compromisos_fijos", []):
        if not c.get("activo", True):
            continue
        dia = c.get("dia_cobro", 0)
        if not dia:
            continue
        try:
            fecha_evento = datetime.date(año_target, mes_target, min(dia, 28)).isoformat()
            resultado = await tool_calendar_crear_evento_pago({
                "titulo": c["nombre"],
                "fecha": fecha_evento,
                "importe": abs(c["importe_mensual"]),
                "descripcion": c.get("alerta", "")
            }, http_client)
            creados.append(resultado)
        except Exception as e:
            errores.append({"nombre": c["nombre"], "error": str(e)})

    return {
        "mes_sincronizado": f"{año_target}-{mes_target:02d}",
        "eventos_creados": len(creados),
        "errores": len(errores),
        "detalle_errores": errores
    }


async def tool_finanzas_perfil(http_client: httpx.AsyncClient) -> dict:
    """Devuelve el perfil financiero"""
    finanzas = _cargar_finanzas()
    return {
        "perfil": finanzas["perfil_financiero"],
        "pagos_especiales_pendientes": finanzas.get("pagos_especiales_pendientes", []),
        "num_compromisos_activos": sum(
            1 for c in finanzas.get("compromisos_fijos", []) 
            if c.get("activo", True)
        )
    }


# ─── Router de Herramientas ────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "finanzas_registrar_gasto": tool_finanzas_registrar_gasto,
    "finanzas_registrar_ingreso": tool_finanzas_registrar_ingreso,
    "finanzas_resumen_mes": tool_finanzas_resumen_mes,
    "finanzas_proximos_pagos": tool_finanzas_proximos_pagos,
    "finanzas_estado_deudas": tool_finanzas_estado_deudas,
    "telegram_enviar_mensaje": tool_telegram_enviar_mensaje,
    "telegram_enviar_resumen_semanal": tool_telegram_enviar_resumen_semanal,
    "sheets_sync_movimientos": tool_sheets_sync_movimientos,
    "calendar_crear_evento_pago": tool_calendar_crear_evento_pago,
    "calendar_sincronizar_compromisos": tool_calendar_sincronizar_compromisos,
    "finanzas_perfil": tool_finanzas_perfil,
}


# ─── FastAPI App ───────────────────────────────────────────────────────────────

http_client: httpx.AsyncClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización al arrancar"""
    global http_client
    
    logger.info("=" * 50)
    logger.info("Finanzas MCP HTTP Server starting...")
    logger.info(f"Database: {FINANZAS_JSON}")
    
    if not FINANZAS_JSON.exists():
        logger.error(f"ERROR: {FINANZAS_JSON} not found!")
        raise RuntimeError(f"Database not found: {FINANZAS_JSON}")
    
    http_client = httpx.AsyncClient(timeout=30.0)
    
    logger.info("✓ Server ready")
    logger.info("Available tools: " + ", ".join(TOOL_HANDLERS.keys()))
    
    yield
    
    await http_client.aclose()
    logger.info("Server shutdown")


app = FastAPI(
    title="Finanzas MCP Server",
    description="Servidor HTTP independiente del MCP de finanzas",
    version="1.0.0",
    lifespan=lifespan
)


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "running"}


@app.post("/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest):
    """Ejecuta una herramienta del MCP de finanzas"""
    logger.info(f"Executing tool: {request.tool}")
    
    handler = TOOL_HANDLERS.get(request.tool)
    if not handler:
        logger.warning(f"Tool not found: {request.tool}")
        return ExecuteResponse(
            status="error",
            message=f"Tool '{request.tool}' no encontrada. Herramientas disponibles: {', '.join(TOOL_HANDLERS.keys())}"
        )
    
    try:
        import inspect
        sig = inspect.signature(handler)
        if len(sig.parameters) == 1:
            result = await handler(request.payload)
        else:
            result = await handler(request.payload, http_client)
        
        return ExecuteResponse(status="ok", result=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing {request.tool}: {e}")
        return ExecuteResponse(
            status="error",
            message=str(e)
        )


# ─── Arranque ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "31434"))
    host = os.environ.get("HOST", "0.0.0.0")
    log_level = os.environ.get("LOG_LEVEL", "info")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level.lower()
    )
