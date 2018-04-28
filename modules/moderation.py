from .module import Module, Command, QueueAction
import asyncio
import discord

class ModerationModule(Module):
    def __init__(self):
        super().__init__(name='Moderation',description='Commands related to moderation',category='moderation')
        self.commands = {
            'mute': Mute()
        }

class Mute(Command):
    def __init__(self):
        super().__init__(name='mute',description='`!mute @user reason`')
        self.permission = 'admin'
    def run(self,command,msg,settings):
        self.reset()
        not_found = 'Sorry <@!{0}> couldn\'t find that user'.format(msg.author.id)
        args = msg.content.split(' ')
        success = True
        try:
            user_raw = args[1]
        except KeyError:
            self.content = not_found
            success = False
        if success:
            if user_raw.startswith('<@!'):
                user_id = user_raw[3:-1]
                self.content = '<@!{0}> muting <@!{1}>'.format(msg.author.id,user_id)
                self.queue = [QueueAction(mute_member,[user_id,msg.server.id])]
            elif user_raw.startswith('<@'):
                user_id = user_raw[2:-1]
                self.content = '<@!{0}> muting <@!{1}>'.format(msg.author.id,user_id)
                self.queue = [QueueAction(mute_member,[user_id,msg.server.id])]
            else:
                self.content = not_found

@asyncio.coroutine
def mute_member(client,member_id,server_id):
    role = yield from mute_role(client,server_id)
    user = discord.Object(member_id)
    user.server = discord.Object(server_id)
    try:
        yield from client.server_voice_state(user,mute=True)
        yield from client.add_roles(user,role)
    except:
        print('Unable to mute user')
@asyncio.coroutine
def mute_role(client,server_id):
    server = client.get_server(server_id)
    role_name = 'bot_mute'
    if server != None:
        role_names = []
        for role in server.roles:
            role_names.append(role.name)
            if role.name == role_name:
                value = role
        if not role_name in role_names:
            perms = discord.Permissions(send_messages=False,send_tts_messages=False)
            try:
                value = yield from client.create_role(server,name=role_name,hoist=False,mentionable=False,permissions=perms)
                try:
                    yield from client.move_role(server,value,1)
                except:
                    pass
            except:
                value = None
    else:
        value = None
    return value
