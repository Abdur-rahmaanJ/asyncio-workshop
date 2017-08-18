import json

import asyncio
import aiohttp_autoreload
from aiohttp import (
    web,
    WSMsgType
)


connections = set()


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # ws.close() - closes connection
    # ws.send_str(str) - sends a str
    connections.add(ws)

    async for msg in ws:
        # msg.type - type of a message. See WSMsgType
        # msg.data - data received

        if msg.type == WSMsgType.TEXT:
            data = json.loads(msg.data)
            for connection in connections:
                await connection.send_json(data)
        elif msg.type == WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())
        elif msg.type == WSMsgType.CLOSED:
            print('closing connection')
            connections.remove(ws)

    return ws


async def index(request):
    return web.FileResponse('./index.html')


async def css(request):
    return web.FileResponse('./static/style.css')


async def reconnecting_websocket(request):
    return web.FileResponse('./static/reconnecting-websocket.min.js')


async def members(request):
    return web.json_response([])


async def rooms(request):
    return web.json_response([])


def create_app(loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    app = web.Application(loop=loop)
    app.router.add_get('/', index)
    app.router.add_get('/members', members)
    app.router.add_get('/rooms', rooms)
    app.router.add_get('/style.css', css)
    app.router.add_get('/reconnecting-websocket.min.js', reconnecting_websocket)
    app.router.add_get('/ws', websocket_handler)
    return app


if __name__ == '__main__':
    app = create_app()
    aiohttp_autoreload.start(app.loop)
    web.run_app(app, port=8080)
