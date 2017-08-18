import json
import asyncio

from aiohttp import (
    web,
    WSMsgType,
)


class ChatMember(object):
    def __init__(self, nickname, connection):
        self.connection = connection
        self.nickname = nickname

    async def send_message(self, data):
        return self.connection.send_json(data)


class ChatRoom(object):

    def __init__(self, name, members=None, messages=None):
        self.name = name
        self.members = members or {}
        self.messages = messages or []

    @property
    def empty(self):
        return len(self.members) == 0

    async def add_member(self, member):
        self.members[member.nickname] = member
        for message in self.messages:
            await member.send_message(message)
        await self.send_message({
            'message': 'User {} joined room {}!'.format(member.nickname, self.name),
            'room': self.name,
            'from': 'Server'
        })

    async def remove_member(self, nickname):
        if self.is_member(nickname):
            del self.members[nickname]
            await self.send_message({
                'message': 'User {} left room {}!'.format(nickname, self.name),
                'room': self.name,
                'from': 'Server'
            })

    def is_member(self, nickname):
        return nickname in self.members

    async def send_message(self, data):
        data['room'] = self.name
        self.messages.append(data)
        for member in self.members.values():
            await member.send_message(data)


class ChatHandler(object):

    GLOBAL_ROOM_NAME = 'global'

    def __init__(self):
        self.rooms = {}
        self.members = {}

    async def join_chat_room(self, room_name, nickname):
        member = self.members.get(nickname)
        if member:
            if room_name not in self.rooms:
                self.rooms[room_name] = ChatRoom(room_name)
            return await self.rooms[room_name].add_member(member)

    async def leave_chat_room(self, room_name, nickname):
        room = self.rooms.get(room_name)
        if room:
            await room.remove_member(nickname)
            if room.empty:
                loop = asyncio.get_event_loop()
                loop.call_later(15, self.remove_room_if_empty, room_name)

    def remove_room_if_empty(self, room_name):
        room = self.rooms.get(room_name)
        if room and room.empty:
            del self.rooms[room_name]

    async def handle_error(self, msg, member):
        print('ws connection closed with exception %s' % member.connection.exception())
        return self.handle_disconnect(member)

    async def handle_text_message(self, msg, member):
        data = json.loads(msg.data)
        message = data.pop('message', '')
        room_name = data.pop('room', self.GLOBAL_ROOM_NAME)
        room = self.rooms.get(room_name)
        if room and room.is_member(member.nickname):
            await room.send_message({
                'message': message,
                'from': member.nickname
            })

    async def handle_disconnect(self, member):
        del self.members[member.nickname]
        for room_name in self.rooms:
            await self.leave_chat_room(room_name, member.nickname)

    async def handle(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        nickname = request.query.get('nickname', 'anonymous')
        member = ChatMember(nickname, ws)
        self.members[member.nickname] = member
        # during first phase
        await self.join_chat_room(self.GLOBAL_ROOM_NAME, member.nickname)

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self.handle_text_message(msg, member)
                elif msg.type == WSMsgType.ERROR:
                    await self.handle_error(msg, member)
        finally:
            await self.handle_disconnect(member)
        return ws
