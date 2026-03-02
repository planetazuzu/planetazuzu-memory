#!/usr/bin/env python3
"""Cronjob: monitorear correos nuevos cada 15 minutos"""
import asyncio
import sys
sys.path.insert(0, '/root/gmail_mcp')

from server_http import tool_gmail_monitorizar_nuevos, http_client
import httpx

async def main():
    async with httpx.AsyncClient(timeout=60.0) as http:
        result = await tool_gmail_monitorizar_nuevos({}, http)
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
