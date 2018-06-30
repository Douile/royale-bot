import asyncio

@asyncio.coroutine
def count_client_users(client,unique=True):
    if unique:
        users = yield from count_client_users_unique(client)
    else:
        users = yield from count_client_users_fast(client)
    return users

@asyncio.coroutine
def count_client_users_unique(client):
    users = []
    for server in client.servers:
        for member in server.members:
            if not member.id in users:
                users.append(member.id)
    return len(users)

@asyncio.corountine
def count_client_users_fast(client):
    users = 0
    for server in client.servers:
        users += server.member_count
    return users
