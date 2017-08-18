import asyncio
import aiohttp_autoreload
from aiohttp import web

from models import ChatHandler


class ChatApplication(web.Application):
    def __init__(self, *, chat_handler=None, **kwargs):
        super().__init__(**kwargs)
        self.chat_handler = chat_handler or ChatHandler()


async def index(request):
    return web.FileResponse('./index.html')


async def css(request):
    return web.FileResponse('./static/style.css')


async def reconnecting_websocket(request):
    return web.FileResponse('./static/reconnecting-websocket.min.js')


async def members(request):
    handler = request.app.chat_handler
    return web.json_response(list(sorted(handler.members.keys())))


async def rooms(request):
    handler = request.app.chat_handler
    nickname = request.query.get('nickname')
    return web.json_response([{
        'name': room.name,
        'present': room.is_member(nickname)
    } for room in handler.rooms.values()])


async def join_room(request):
    handler = request.app.chat_handler
    nickname = request.query.get('nickname')
    data = await request.post()
    room_name = data.get('name')
    if room_name and nickname:
        await handler.join_chat_room(room_name, nickname)
    return web.json_response({'status': 'success'})


async def leave_room(request):
    handler = request.app.chat_handler
    nickname = request.query.get('nickname')
    data = await request.post()
    room_name = data.get('name')
    if room_name and nickname:
        await handler.leave_chat_room(room_name, nickname)
    return web.json_response({'status': 'success'})


def create_app(loop=None, chat_handler=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    app = ChatApplication(loop=loop, chat_handler=chat_handler)
    app.router.add_get('/', index)
    app.router.add_get('/members', members)
    app.router.add_get('/rooms', rooms)
    app.router.add_post('/room', join_room)
    app.router.add_post('/join-room', join_room)
    app.router.add_post('/leave-room', leave_room)
    app.router.add_get('/style.css', css)
    app.router.add_get('/reconnecting-websocket.min.js', reconnecting_websocket)
    app.router.add_get('/ws', app.chat_handler.handle)
    return app


if __name__ == '__main__':
    app = create_app()
    aiohttp_autoreload.start(app.loop)
    web.run_app(app, port=8080)
