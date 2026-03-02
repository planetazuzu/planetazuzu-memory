#!/usr/bin/env python3
"""
cronjobs/gmail_alertas.py - Tareas programadas para Gmail MCP
"""

import sys
import os
from pathlib import Path

# Añadir el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import asyncio
import httpx
import google.auth.transport.requests
from google.oauth2 import service_account
import datetime

# Cargar variables desde .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            if key not in os.environ:
                os.environ[key] = val

TOKEN_PATH = Path("/root/gmail_mcp/token.json")
CREDENTIALS_PATH = Path("/root/gmail_mcp/credentials.json")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GOOGLE_SHEETS_ID = os.environ.get("GOOGLE_SHEETS_ID", "")
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

# Etiquetas
ETIQUETAS_AREAS = ["AREA_FINANZAS", "AREA_PERSONAL", "AREA_PROFESIONAL", "AREA_TECNICA", "AREA_APRENDIZAJE"]
ETIQUETAS_TIPO = ["TIPO_FACTURA", "TIPO_CONTRATO", "TIPO_LEGAL", "TIPO_NOTIFICACION", "TIPO_ACCESO", "TIPO_PROPUESTA", "TIPO_RENOVACION", "TIPO_REUNION", "TIPO_SUSCRIPCION"]
ETIQUETAS_ESTADO = ["ESTADO_PENDIENTE", "ESTADO_ESPERANDO", "ESTADO_RESUELTO"]
URGENTES = ["banco", "hacienda", "deuda", "cobro", "jurídico", "abogado", "demanda", "multa", "seguro", "robo", "fraude", "card", "visa", "préstamo", "crédito"]


def load_credentials():
    if CREDENTIALS_PATH.exists():
        return json.loads(CREDENTIALS_PATH.read_text())
    return None

def load_token():
    if TOKEN_PATH.exists():
        return json.loads(TOKEN_PATH.read_text())
    return None

async def get_gmail_token(http, credentials):
    token = load_token()
    if not token:
        return None
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
        new_token = resp.json()
        new_token["expires_at"] = datetime.datetime.now().timestamp() + new_token["expires_in"]
        TOKEN_PATH.write_text(json.dumps(new_token))
        return new_token["access_token"]
    return token["access_token"]

def inferir_etiquetas(asunto, remitente, snippet):
    texto = f"{asunto} {remitente} {snippet}".lower()
    
    area = "AREA_PERSONAL"
    if any(p in texto for p in ["trabajo", "empresa", "cv", "entrevista", "jefe"]):
        area = "AREA_PROFESIONAL"
    elif any(p in texto for p in ["factura", "banco", "préstamo", "hipoteca", "inversión", "nómina", "hacienda"]):
        area = "AREA_FINANZAS"
    elif any(p in texto for p in ["github", "codigo", "tech", "developer", "api", "server"]):
        area = "AREA_TECNICA"
    elif any(p in texto for p in ["curso", "udemy", "coursera", "libro", "aprender", "estudio"]):
        area = "AREA_APRENDIZAJE"
    
    tipo = "TIPO_NOTIFICACION"
    if any(p in texto for p in ["factura", "recibo", "invoice", "importe"]):
        tipo = "TIPO_FACTURA"
    elif any(p in texto for p in ["contrato", "acuerdo", "términos"]):
        tipo = "TIPO_CONTRATO"
    elif any(p in texto for p in ["legal", "abogado", "demanda", "sentencia"]):
        tipo = "TIPO_LEGAL"
    elif any(p in texto for p in ["acceso", "password", "usuario", "cuenta"]):
        tipo = "TIPO_ACCESO"
    elif any(p in texto for p in ["propuesta", "oferta", "presupuesto"]):
        tipo = "TIPO_PROPUESTA"
    elif any(p in texto for p in ["renovación", "renovar", "vencimiento"]):
        tipo = "TIPO_RENOVACION"
    elif any(p in texto for p in ["reunión", "meeting", "calendar"]):
        tipo = "TIPO_REUNION"
    elif any(p in texto for p in ["suscripción", "suscripcion", "suscrito", "premium"]):
        tipo = "TIPO_SUSCRIPCION"
    
    estado = "ESTADO_PENDIENTE"
    if any(p in texto for p in ["resuelto", "completado", "hecho", "ok"]):
        estado = "ESTADO_RESUELTO"
    elif any(p in texto for p in ["esperando", "pendiente de", "a la espera"]):
        estado = "ESTADO_ESPERANDO"
    
    return {"area": area, "tipo": tipo, "estado": estado}

def es_urgente(asunto, remitente, snippet):
    texto = f"{asunto} {remitente} {snippet}".lower()
    return any(p in texto for p in URGENTES)

async def obtener_id_etiquetas(http, token):
    resp = await http.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/labels",
        headers={"Authorization": f"Bearer {token}"}
    )
    return {l["name"]: l["id"] for l in resp.json().get("labels", [])}


async def tarea_monitorizar():
    """Monitorea correos nuevos cada 15 minutos"""
    async with httpx.AsyncClient(timeout=30) as http:
        credentials = load_credentials()
        if not credentials:
            print("⚠️ No hay credenciales OAuth configuradas")
            return
        
        try:
            token = await get_gmail_token(http, credentials)
            if not token:
                print("⚠️ No hay token de acceso")
                return
                
            ids_etiquetas = await obtener_id_etiquetas(http, token)
            
            hace_2_horas = int((datetime.datetime.now() - datetime.timedelta(hours=2)).timestamp())
            resp = await http.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers={"Authorization": f"Bearer {token}"},
                params={"maxResults": 50, "q": f"after:{hace_2_horas}"}
            )
            mensajes = resp.json().get("messages", [])
            
            if not mensajes:
                print(f"✅ Sin correos nuevos")
                return
            
            nuevos = 0
            urgentes = []
            
            for msg in mensajes:
                try:
                    resp = await http.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    msg_data = resp.json()
                    
                    tiene_area = any(lid in ids_etiquetas.values() for lid in msg_data.get("labelIds", []))
                    if tiene_area:
                        continue
                    
                    asunto = ""
                    remitente = ""
                    snippet = msg_data.get("snippet", "")
                    
                    for header in msg_data.get("payload", {}).get("headers", []):
                        if header["name"].lower() == "subject":
                            asunto = header["value"]
                        if header["name"].lower() == "from":
                            remitente = header["value"]
                    
                    etiquetas = inferir_etiquetas(asunto, remitente, snippet)
                    
                    label_ids = []
                    for key in ["area", "tipo", "estado"]:
                        nombre = etiquetas[key]
                        if nombre in ids_etiquetas:
                            label_ids.append(ids_etiquetas[nombre])
                    
                    await http.post(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}/modify",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"addLabelIds": label_ids}
                    )
                    
                    nuevos += 1
                    if es_urgente(asunto, remitente, snippet):
                        urgentes.append({"asunto": asunto[:50], "remitente": remitente[:30]})
                        
                except Exception:
                    pass
            
            if urgentes:
                msg_urg = "🚨 *Correos urgentes*\n\n"
                for u in urgentes[:5]:
                    msg_urg += f"• {u['asunto']}...\n"
                await http.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": TELEGRAM_CHAT_ID, "text": msg_urg, "parse_mode": "Markdown"}
                )
            
            print(f"✅ Monitorizado: {nuevos} nuevos, {len(urgentes)} urgentes")
            
        except Exception as e:
            print(f"⚠️ Error: {e}")


async def tarea_resumen():
    """Resumen matutino diario a las 8:00"""
    async with httpx.AsyncClient(timeout=30) as http:
        credentials = load_credentials()
        if not credentials:
            print("⚠️ No hay credenciales")
            return
        
        try:
            token = await get_gmail_token(http, credentials)
            if not token:
                return
                
            ids_etiquetas = await obtener_id_etiquetas(http, token)
            
            resp = await http.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers={"Authorization": f"Bearer {token}"},
                params={"maxResults": 500, "q": "label:ESTADO_PENDIENTE"}
            )
            mensajes = resp.json().get("messages", [])
            
            por_area = {}
            por_tipo = {}
            
            for msg in mensajes[:100]:
                try:
                    resp = await http.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    msg_data = resp.json()
                    
                    for nombre, lid in ids_etiquetas.items():
                        if lid in msg_data.get("labelIds", []):
                            if nombre.startswith("AREA_"):
                                por_area[nombre] = por_area.get(nombre, 0) + 1
                            elif nombre.startswith("TIPO_"):
                                por_tipo[nombre] = por_tipo.get(nombre, 0) + 1
                except:
                    pass
            
            msg = "📧 *RESUMEN MATUTINO*\n\n*Por ÁREA:*\n"
            for area, count in sorted(por_area.items(), key=lambda x: -x[1]):
                msg += f"  📁 {area.replace('AREA_', '')}: {count}\n"
            msg += "\n*Por TIPO:*\n"
            for tipo, count in sorted(por_tipo.items(), key=lambda x: -x[1]):
                msg += f"  🏷️ {tipo.replace('TIPO_', '')}: {count}\n"
            msg += f"\n_Total: {len(mensajes)}_"
            
            await http.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
            )
            
            print(f"✅ Resumen enviado: {len(mensajes)} pendientes")
            
        except Exception as e:
            print(f"⚠️ Error: {e}")


TAREAS = {
    "monitorizar": tarea_monitorizar,
    "resumen": tarea_resumen,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in TAREAS:
        print(f"Uso: python gmail_alertas.py [{' | '.join(TAREAS.keys())}]")
        sys.exit(1)
    asyncio.run(TAREAS[sys.argv[1]]())
