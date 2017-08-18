import json

from aiohttp import (
    web,
    WSMsgType
)


class ChatMember(object):
    def __init__(self, nickname, connection):
        self.connection = connection
        self.nickname = nickname

    async def send_message(self, data):
        return self.connection.send_json(data)


class ChatRoom(object):

    def __init__(self, name):
        self.name = name
        self.members = {}
        self.messages = []

    def add_member(self, member):
        self.members[member.nickname] = member

    def remove_member(self, nickname):
        if self.is_member(nickname):
            del self.members[nickname]

    def is_member(self, nickname):
        return nickname in self.members

    async def send_message(self, data):
        for member in self.members.values():
            self.messages.append(data)
            await member.send_message(data)


class ChatHandler(object):

    GLOBAL_ROOM_NAME = 'global'

    def __init__(self):
        self.rooms = {}
        self.members = {}

    def join_chat_room(self, room_name, nickname):
        member = self.members.get(nickname)
        if member:
            if room_name not in self.rooms:
                self.rooms[room_name] = ChatRoom(room_name)
            self.rooms[room_name].add_member(member)

    def leave_chat_room(self, room_name, nickname):
        room = self.rooms.get(room_name)
        if room:
            room.remove_member(nickname)

    async def handle_error(self, msg, member):
        print('ws connection closed with exception %s' % member.connection.exception())
        return self.handle_disconnect(msg, member)

    async def handle_text_message(self, msg, member):
        data = json.loads(msg.data)
        message = data.pop('message', '')
        room_name = data.pop('room', self.GLOBAL_ROOM_NAME)
        room = self.rooms.get(room_name)
        if room and room.is_member(member.nickname):
            await room.send_message({
                'message': message,
                'nickname': member.nickname
            })

    async def handle_disconnect(self, msg, member):
        for room in self.rooms:
            room.remove_member(member)

    async def handle(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        nickname = request.query.get('nickname', 'anonymous')
        member = ChatMember(nickname, ws)
        self.members[member.nickname] = member
        # during first phase
        self.join_chat_room(self.GLOBAL_ROOM_NAME, member.nickname)
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                await self.handle_text_message(msg, member)
            elif msg.type == WSMsgType.ERROR:
                await self.handle_error(msg, member)
            elif msg.type == WSMsgType.CLOSED:
                await self.handle_disconnect(msg, member)
        return ws
