import os
import asyncio
from aiohttp import web, WSMsgType

clients = set()


async def index(request):
    return web.Response(text="Internet Chat Server is running!")


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    clients.add(ws)

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                message = msg.data

                # Send message to everyone except sender
                for client in list(clients):
                    if client != ws and not client.closed:
                        await client.send_str(message)

            elif msg.type == WSMsgType.ERROR:
                print("WebSocket error:", ws.exception())

    finally:
        clients.discard(ws)

    return ws


app = web.Application()

app.router.add_get("/", index)
app.router.add_get("/chat", websocket_handler)

port = int(os.environ.get("PORT", 10000))

web.run_app(app, host="0.0.0.0", port=port)