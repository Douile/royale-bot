from .module import Module, Command, QueueAction, parse_user_at
import asyncio
import discord
import async_timeot

class ModerationModule(Module):
    def __init__(self):
        super().__init__(name='Moderation',description='Commands related to moderation',category='moderation')
        self.commands = {
            'mute': Mute(),
            'kick': Kick(),
            'analytics': Analytics()
        }

class Mute(Command):
    def __init__(self):
        super().__init__(name='mute',description='Globally mute a user. `{prefix}mute [@user] [reason]`')
        self.permission = 'admin'
    def run(self,command,msg,settings):
        self.reset()
        not_found = 'Sorry <@!{author}> couldn\'t find that user'
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
                self.content = '<@!{author}> muting <@!{0}>'.format(user_id)
                self.queue = [QueueAction(mute_member,[user_id,msg.server.id])]
            elif user_raw.startswith('<@'):
                user_id = user_raw[2:-1]
                self.content = '<@!{author}> muting <@!{0}>'.format(user_id)
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

class Kick(Command):
    def __init__(self):
        super().__init__(name='kick',description='Kick a user from the server.`{prefix}kick @user reason...`',permission='admin')
    @asyncio.coroutine
    def run(self,command,msg,settings):
        l = len('kick ')
        data = command[l:]
        try:
            s = data.index(' ')
        except ValueError:
            s = -1
        if s > -1:
            user = data[:s]
            reason = data[s+1:]
            print('Kick {0} : {1}'.format(user,reason))
            user_ob = parse_user_at(user,msg.server.id)
            member = msg.server.get_member(user_ob.id)
            kicker = msg.author.nick
            if kicker == None:
                kicker = msg.author.display_name
            self.content = '<@!{0}> kicked {1}'.format('{author}',user)
            self.queue = [QueueAction(kick_user,[member,kicker,reason])]
        else:
            self.content = '<@!{author}> Invalid arguments'

@asyncio.coroutine
def kick_user(client,user,kicker,reason):
    kickmsg = '<@!{0}> You were kicked by @{1} for: {2}'.format(user.id,kicker,reason)
    print(kickmsg)
    yield from client.send_message(user,content=kickmsg)
    yield from client.kick(user)

class Analytics(Command):
    def __init__(self):
        super().__init__(name='analytics',description='Get server analytics. `{prefix}analytics`',permission='admin')
    @asyncio.coroutine
    def run(self,command,msg,settings):
        self.embed = AnalyticsEmbed(msg.server.name,msg.server.icon_url)
        self.embed.update_region(str(msg.server.region))
        self.embed.set_members(msg.server.member_count)
        for i in [1,7,30,365]:
            try:
                count = yield from asyncio.wait_for(client.estimate_pruned_members(msg.server,days=i),10.0)
            except HTTPException:
                count = 'Unknown'
            print('Got pruned members for {} days: {}'.format(i,count))
            self.embed.set_inactive(i,count)
        if msg.server.large:
            offline = 'Server too big'
        else:
            offline = yield from client.request_offline_members(msg.server)
        self.embed.set_offline(offline)
        self.embed.parse_config()

class AnalyticsEmbed(discord.Embed):
    def __init__(self,servername,servericon):
        super().__init__(title=servername,color=0xff7f23)
        self.set_thumbnail(url=servericon)
        self.config_data = {}
    def parse_config(self):
        self.clear_fields()
        print('Parsing analytics embed: {}'.format(self.config_data))
        self.add_data('Total members',self.config_data.get('members',0))
        self.add_data('Offline members',self.config_data.get('offline_members',0))
        self.add_data('Inactive members (1 day)',self.config_data.get('inactive_1',0))
        self.add_data('Inactive members (1 week)',self.config_data.get('inactive_7',0))
        self.add_data('Inactive members (1 month)',self.config_data.get('inactive_30',0))
        self.add_data('Inactive members (1 year)',self.config_data.get('inactive_365',0))
    def add_data(self,name,value):
        self.add_field(name=name,value=value,inline=True)
    def update_region(self,region):
        self.description = self.parse_region(region)
    def set_inactive(self,days,amount):
        key = 'inactive_{}'.format(days)
        self.config_data[key] = amount
    def set_members(self,amount):
        self.config_data['members'] = amount
    def set_offline(self,amount):
        self.config_data['offline_members'] = amount
    @staticmethod
    def parse_region(region):
        r = str(region).lower()
        if r == 'singapore':
            flag = ':flag_sg:'
        elif r == 'london':
            flag = ':flag_gb:'
        elif r == 'sydney':
            flag = ':flag_au:'
        elif r == 'amsterdam':
            flag = ':flag_nl:'
        elif r == 'frankfurt':
            flag = ':flag_de:'
        elif r == 'brazil':
            flag = ':flag_br:'
        elif r.startswith('us'):
            flag = ':flag_us:'
        elif r.startswith('eu'):
            flag = ':flag_eu:'
        elif r.startswith('vip-us'):
            flag = ':moneybag::flag_us:'
        elif r == 'vip-amsterdam':
            flag = ':moneybag::flag_nl:'
        else:
            flag = ':question:{}'.format(region)
        return flag
