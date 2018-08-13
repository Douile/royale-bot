import asyncio
from discord import Object

PRIORITY_LIMIT = 10

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

@asyncio.coroutine
def count_client_users_fast(client):
    users = 0
    for server in client.servers:
        users += server.member_count
    return users

@asyncio.coroutine
def get_server_priority(servers,get_priority):
    servers_parsed = []
    used = []
    priority = 0
    done = False
    while priority < PRIORITY_LIMIT and done == False:
        servers_p = get_priority(priority)
        if len(servers_p) > 0:
            servers_r = []
            for server in servers_p:
                id = server.get('server_id')
                if not id in used:
                    used.append(id)
                    servers_r.append(Object(id))
            servers_parsed.append(servers_r)
        else:
            done = True
        priority += 1
    servers_r = []
    for server in servers:
        if not server.id in used:
            servers_r.append(Object(server.id))
    servers_parsed.append(servers_r)
    return servers_parsed
