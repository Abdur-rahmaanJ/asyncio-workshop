from .models import ChatHandler, ChatRoom
from .app import create_app


async def test_receives_sent_message(test_client):
    client = await test_client(create_app)
    connection = await client.ws_connect('/ws?nickname=JohnDoe')

    # lets swallow welcome message
    await connection.receive_json(timeout=0.2)
    message = 'Hello, world!'
    await connection.send_json({'message': message, 'from': 'JohnDoe'})
    response = await connection.receive_json(timeout=0.2)

    assert response['message'] == message


async def test_other_user_receives_message(test_client):
    client = await test_client(create_app)
    first_connection = await client.ws_connect('/ws?nickname=JohnDoe')
    second_connection = await client.ws_connect('/ws?nickname=FooBar')

    # lets swallow welcome message
    await second_connection.receive_json(timeout=0.2)

    # lets swallow second user welcome message
    await second_connection.receive_json(timeout=0.2)



    message = 'abc'
    await first_connection.send_json({'message': message, 'from': 'JohnDoe'})
    response = await second_connection.receive_json(timeout=0.2)

    assert response['message'] == message

async def test_get_list_of_nicknames(test_client):
    client = await test_client(create_app)

    await client.ws_connect('/ws?nickname=JohnDoe')
    await client.ws_connect('/ws?nickname=FooBar')

    response = await client.get('/members')
    data = await response.json()
    assert data == [
        'FooBar',
        'JohnDoe'
    ]


async def test_get_previous_messages_on_room_join(test_client):
    previous_message = {'message': 'Test', 'nickname': 'Alibaba'}
    room = ChatRoom('global', messages=[previous_message])
    handler = ChatHandler()
    handler.rooms['global'] = room

    client = await test_client(create_app, chat_handler=handler)
    connection = await client.ws_connect('/ws?nickname=JohnDoe')
    data = await connection.receive_json(timeout=0.2)
    assert data == previous_message

async def test_get_list_of_rooms(test_client):
    handler = ChatHandler()
    handler.rooms['test'] = ChatRoom('test')

    client = await test_client(create_app, chat_handler=handler)

    response = await client.get('/rooms')
    data = await response.json()
    assert data == [{
        'name': 'test',
        'present': False
    }]
