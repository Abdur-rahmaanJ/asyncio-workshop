from .app import create_app


async def test_receives_sent_message(test_client):
    client = await test_client(create_app)
    connection = await client.ws_connect('/ws?nickname=JohnDoe')

    message = 'Hello, world!'
    await connection.send_json({'message': message, 'from': 'JohnDoe'})
    response = await connection.receive_json(timeout=0.2)

    assert response['message'] == message


async def test_other_user_receives_message(test_client):
    client = await test_client(create_app)
    first_connection = await client.ws_connect('/ws?nickname=JohnDoe')
    second_connection = await client.ws_connect('/ws?nickname=FooBar')

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
