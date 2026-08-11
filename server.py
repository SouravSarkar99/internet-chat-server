import os
from aiohttp import web, WSMsgType

clients = {}


async def index(request):
    return web.Response(text="🌐 Internet Chat Server is running!")


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    username = None

    try:
        # First message = username
        msg = await ws.receive()

        if msg.type != WSMsgType.TEXT:
            await ws.close()
            return ws

        username = msg.data.strip()

        if not username:
            username = "Anonymous"

        # Make username unique
        original_name = username
        counter = 2

        while username in clients.values():
            username = f"{original_name}{counter}"
            counter += 1

        clients[ws] = username

        print(f"{username} joined the chat.")

        # Tell everyone that user joined
        for client in list(clients):
            if client != ws and not client.closed:
                await client.send_json({
                    "type": "system",
                    "message": f"{username} joined the chat."
                })

        # Main message loop
        async for msg in ws:

            if msg.type == WSMsgType.TEXT:

                message = msg.data.strip()

                if not message:
                    continue

                # Send message to everyone
                for client in list(clients):
                    if not client.closed:
                        await client.send_json({
                            "type": "message",
                            "username": username,
                            "message": message
                        })

            elif msg.type == WSMsgType.ERROR:
                print("WebSocket error:", ws.exception())

    except Exception as e:
        print("Connection error:", e)

    finally:

        if ws in clients:
            username = clients.pop(ws)

            print(f"{username} left the chat.")

            # Notify remaining users
            for client in list(clients):
                if not client.closed:
                    try:
                        await client.send_json({
                            "type": "system",
                            "message": f"{username} left the chat."
                        })
                    except:
                        pass

    return ws


app = web.Application()

app.router.add_get("/", index)
app.router.add_get("/chat", websocket_handler)

port = int(os.environ.get("PORT", 10000))

web.run_app(
    app,
    host="0.0.0.0",
    port=port
)
