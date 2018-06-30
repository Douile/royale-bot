
def count_users(client):
    users = []
    for server in client.servers:
        for member in server.members:
            if not member.id in users:
                users.append(member.id)
    return len(users)
