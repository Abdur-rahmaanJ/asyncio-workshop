import json

import asyncio
import aiohttp_autoreload
from aiohttp import web

from projekt.models import ChatHandler

handler = ChatHandler()


async def index(request):
    return web.FileResponse('./index.html')


async def css(request):
    return web.FileResponse('./static/style.css')


async def reconnecting_websocket(request):
    return web.FileResponse('./static/reconnecting-websocket.min.js')


async def members(request):
    return web.json_response(list(sorted(handler.members.keys())))


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
    app.router.add_get('/ws', handler.handle)
    return app


if __name__ == '__main__':
    app = create_app()
    aiohttp_autoreload.start(app.loop)
    web.run_app(app, port=8080)
