"""
Lightweight HTTP verification API.
Your external application hits this to validate a key + HWID combo.

Endpoints:
  POST /verify   { "key": "...", "discord_id": "...", "hwid": "..." }
  GET  /health

Run alongside the bot:  python api.py
"""

from aiohttp import web
import asyncio
import os
from database import init_db, is_key_valid, log_action

API_SECRET = os.getenv("API_SECRET", "change_this_secret")
API_PORT   = int(os.getenv("API_PORT", "8080"))


async def handle_verify(request: web.Request) -> web.Response:
    # Check shared secret header
    secret = request.headers.get("X-API-Secret", "")
    if secret != API_SECRET:
        return web.json_response({"valid": False, "reason": "Unauthorized."}, status=401)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"valid": False, "reason": "Invalid JSON."}, status=400)

    key        = body.get("key", "").upper().strip()
    discord_id = str(body.get("discord_id", "")).strip()
    hwid       = body.get("hwid", "").strip()

    if not key or not discord_id or not hwid:
        return web.json_response({"valid": False, "reason": "Missing key, discord_id, or hwid."}, status=400)

    valid, reason = await is_key_valid(key, discord_id, hwid)

    await log_action(
        action="API_VERIFY",
        actor=discord_id,
        target=key,
        detail=f"valid={valid} reason={reason} ip={request.remote}"
    )

    return web.json_response({"valid": valid, "reason": reason})


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def start_api():
    await init_db()
    app = web.Application()
    app.router.add_post("/verify", handle_verify)
    app.router.add_get("/health",  handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", API_PORT)
    await site.start()
    print(f"[API] Listening on http://0.0.0.0:{API_PORT}")
    return runner


if __name__ == "__main__":
    async def main():
        runner = await start_api()
        try:
            await asyncio.Event().wait()  # run forever
        finally:
            await runner.cleanup()

    asyncio.run(main())
