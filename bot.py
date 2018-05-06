import discord
import asyncio
import json
import os
import os.path
import sys
import signal
from datetime import datetime
import time
import traceback

from modules import default, fortnite, moderation
from modules.data import shop, meta
from datamanagement import sql

def getEnv(name,default=None):
    value = os.environ.get(name,None)
    if value == None:
        if default == None:
            value = input("Env variable not found, please enter {}: ".format(name))
        else:
            value = default
    return value

#constants
VERSION = "0.0.89"
KEY_DISCORD = getEnv("KEY_DISCORD")
KEY_FNBR = getEnv("KEY_FNBR")
KEY_TRACKERNETWORK = getEnv("KEY_TRACKERNETWORK")
DATABASE_URL = getEnv("DATABASE_URL")
BOT_NAME = getEnv("BOT_NAME","FortniteData")
SHARD_NO = 0
SHARD_COUNT = 1
if len(sys.argv) > 2:
    try:
        SHARD_NO = int(sys.argv[1])
        SHARD_COUNT = int(sys.argv[2])
    except ValueError:
        pass

def checkPermissions(channel,type,settings):
    try:
        if settings[type] == channel or settings[type] == '':
            p = True
        else:
            p = False
    except KeyError:
        p = False
    return p
def get_prefix(settings):
    prefix = settings.get('prefix','!')
    if prefix == None:
        prefix = '!'
    return prefix


class Command():
    def __init__(self):
        self.content = None
        self.file = None
        self.embed = None
        self.embeds = None
        self.settings = None
        self.shutdown = False
        self.typing = False
        self.noPermission = None
        self.queue = []
    def changeSettings(self,settings):
        sets = settings
        if self.settings != None:
            sets = self.settings
        return sets
class SetPresence(Command):
    def __init__(self,msg,settings):
        super().__init__()
        try:
            name = msg.content.split(" ")[1]
            type = msg.content.split(" ")[2]
        except IndexError:
            name = ""
            type = "1"
        try:
            type = int(type)
        except ValueError:
            type = 1
        self.game = discord.Game(name=name,type=type)
        self.content = "Presence changed!"
class Shutdown(Command):
    def __init__(self,msg,settings):
        super().__init__()
        self.content = "OK <@!{0}>. Shutting down...".format(msg.author.id)
        self.shutdown = True
def changes(original={},new={}):
    changed = {}
    for a in new:
        t = type(new[a])
        if t is str or t is int or t is bool:
            try:
                if original[a] == new[a]:
                    changed[a] = False
                else:
                    changed[a] = True
            except KeyError:
                changed[a] = True
        elif t is dict or t is list:
            try:
                changed[a] = changes(original[a],new[a])
            except KeyError:
                changed[a] = {}
                for b in new[a]:
                    changed[a][b] = True
    return changed



client = discord.Client(shard_id=SHARD_NO,shard_count=SHARD_COUNT)
client.queued_actions = []
client.database = sql.Database(url=DATABASE_URL)

@asyncio.coroutine
def autoshop(fnbr_key): # add fnbr not accessable fallback
    yield from client.wait_until_ready()
    while not client.is_closed:
        shopdata = None
        for serverid in client.database.servers():
            server = client.database.server_info(serverid,backgrounds=True,channels=True)
            if 'autoshop' in server['channels']:
                now = time.time()
                if 'next_shop' in server:
                    nextshop = server['next_shop']
                if nextshop == None:
                    nextshop = time.mktime(datetime.now().utctimetuple())
                if now >= nextshop:
                    if shopdata == None:
                        shopdata = shop.getShopData(fnbr_key)
                    if shopdata.type == 'shop':
                        rawtime = shop.getTime(shopdata.data.date)
                        file = shop.filename(rawtime)
                        if not os.path.isfile(file):
                            file = yield from shop.generate(shopdata,server['backgrounds'])
                        content = "Data from <https://fnbr.co/>"
                        yield from client.send_file(discord.Object(server['channels']['autoshop']),file,content=content)
                        nextshoptime = round(time.mktime(rawtime.utctimetuple()) + (60*60*24))
                        client.database.set_server_info(serverid,next_shop=nextshoptime,latest_shop=file)
                    else:
                        print('Error getting shop data {0}: {1}'.format(shopdata.error,shopdata.json))
                        shopdata = None
        print("Autoshop now:{0} next:{1}".format(now,nextshop))
        yield from asyncio.sleep(60*15)

@asyncio.coroutine
def autostatus():
    yield from client.wait_until_ready()
    while not client.is_closed:
        cache_raw = client.database.get_cache("status",once=True)
        if 'status' in cache_raw:
            cache = json.loads(cache_raw['status'])
        else:
            cache = {}
        data = meta.getStatus()
        changed = changes(cache,data)
        client.database.set_cache("status",json.dumps(data),once=True)
        servicechange = []
        for s in changed['services']:
            if changed['services'][s] == True:
                servicechange.append(s)
        embed = None
        if len(servicechange) > 0:
            embed = fortnite.StatusEmbed(data['online'],data['message'])
            for s in servicechange:
                embed.add_service(name=s,value=data['services'][s])
        elif changed['online'] == True or changed['message'] == True:
            embed = fortnite.StatusEmbed(data['online'],data['message'])
        if embed != None:
            for serverid in client.database.servers():
                server = client.database.server_info(serverid,channels=True)
                if 'autostatus' in server['channels']:
                    yield from client.send_message(discord.Object(server['channels']['autostatus']),embed=embed)
        yield from asyncio.sleep(60*2)

@asyncio.coroutine
def autonews():
    yield from client.wait_until_ready()
    while not client.is_closed:
        cache = client.database.get_cache("news",once=False)
        if cache == None:
            cache = []
        data = meta.getNews('en')
        used = []
        embeds = []
        for msg in data['messages']:
            if not msg['title'] in cache:
                embeds.append(fortnite.NewsEmbed(msg,data['updated']))
                client.database.set_cache("news",msg['title'],once=False)
        for serverid in client.database.servers():
            server = client.database.server_info(serverid,channels=True)
            if 'autonews' in server['channels']:
                for embed in embeds:
                    yield from client.send_message(discord.Object(server['channels']['autonews']),embed=embed)
        yield from asyncio.sleep(60*10)

@asyncio.coroutine
def handle_queue():
    yield from client.wait_until_ready()
    while not client.is_closed:
        for queue_item in client.queued_actions:
            args = [client] + queue_item.args
            try:
                yield from queue_item.function(*args)
            except:
                pass
            client.queued_actions.remove(queue_item)
            print('Handled queue action {0} ({1}), {2} remain'.format(str(queue_item.function),str(args),len(client.queued_actions)))
        yield from asyncio.sleep(0.5)

@client.event
@asyncio.coroutine
def on_ready():
    print("--Logged in--\n{0}\n{1}\n--End login info--".format(client.user.name,client.user.id))
    yield from client.edit_profile(username=BOT_NAME)
    yield from client.change_presence(game=discord.Game(name="Serving you since 2018 (!help)",type=0),status="online",afk=False)


@client.event
@asyncio.coroutine
def on_server_join(server):
    client.database.set_server_info(server.id,server_name=server.name)


@client.event
@asyncio.coroutine
def on_server_update(before,after):
    client.database.set_server_info(after.id,server_name=after.name)


@client.event
@asyncio.coroutine
def on_message(msg):
    settings = client.database.server_info(msg.server.id)
    if settings == None:
        prefix = "!"
    else:
        prefix = settings.get("prefix")
        if prefix == None:
            prefix = "!"
    if not msg.author.bot and msg.content.startswith(prefix):
        command = msg.content[len(prefix):]
        yield from commandHandler(command,msg)
@client.event
@asyncio.coroutine
def on_message_edit(before,msg):
    settings = client.database.server_info(msg.server.id)
    if settings == None:
        prefix = "!"
    else:
        prefix = settings.get("prefix")
        if prefix == None:
            prefix = "!"
    if not msg.author.bot and msg.content.startswith(prefix):
        command = msg.content[len(prefix):]
        yield from commandHandler(command,msg)

@asyncio.coroutine
def commandHandler(command,msg):
    command = command.lower()
    serverid = msg.server.id
    serversettings = client.database.server_info(serverid,channels=True,backgrounds=True)
    if serversettings.get("server_name") != msg.server.name:
        client.database.set_server_info(serverid,server_name=msg.server.name)
    output = Command()
    admin = msg.author.server_permissions.administrator or msg.author.id == '293482190031945739'
    if command.startswith("setpresence"):
        if admin:
            yield from client.send_typing(msg.channel)
            output = SetPresence(msg,serversettings)
            yield from client.change_presence(game=output.game,status='online',afk=False)
        else:
            yield from noPermission(msg,None,serversettings)
    elif command.startswith("shutdown"):
        if msg.author.id == '293482190031945739':
            output = Shutdown(msg,serversettings)
        else:
            yield from noPermission(msg,None,serversettings)
    else:
        output = defaultmodule.run(output,command,msg,serversettings)
        if output.content == None and output.embed == None and output.embeds == None:
            for i in range(0,len(cmodules)):
                output = yield from cmodules[i]._run(output,command,msg,serversettings)
        if len(output.queue) > 0:
            client.queued_actions += output.queue
            print('Added queued action')
    if output.settings != None:
        if 'channels' in output.settings:
            for type in output.settings['channels']:
                client.database.set_server_channel(serverid,type,output.settings['channels'][type])
            output.settings.pop('channels')
        if 'backgrounds' in output.settings:
            client.database.set_server_backgrounds(serverid,backgrounds=output.settings.get('backgrounds'))
            output.settings.pop('backgrounds')
        client.database.set_server_info(serverid,**output.settings)
    if output.typing == True:
        yield from client.send_typing(msg.channel)
    if output.noPermission != None:
        yield from noPermission(msg,output.noPermission,serversettings)
    if output.file != None:
        response = yield from client.send_file(msg.channel,output.file,content=output.content)
        yield from client.delete_message(msg)
    elif output.embeds != None:
        for embed in output.embeds:
            response = yield from client.send_message(msg.channel,embed=embed)
        yield from client.delete_message(msg)
    elif output.content != None or output.embed != None:
        try:
            response = yield from client.send_message(msg.channel,content=output.content,embed=output.embed)
        except discord.errors.HTTPException:
            traceback.print_exc()
            if output.embed != None:
                print(json.dumps(output.embed.to_dict()))
            response = yield from client.send_message(msg.channel,content='Sorry there was an error sending response')
        yield from client.delete_message(msg)
    if isinstance(output,default.Help) or isinstance(output,default.AdminHelp):
        client.database.set_server_info(serverid,last_help_msg=response.id,last_help_channel=response.channel.id)
    if output.shutdown == True:
        yield from client.close()
@asyncio.coroutine
def noPermission(msg,type,settings):
    serverid = msg.server.id
    if type == 'shop' or type == 'stats':
        m = '<@!{0}> Please use the set {1} channel <#{2}>'.format(msg.author.id,type,settings['channels']['shop'])
    elif type == 'setchannel' or type == 'resetchannels':
        m = '<@!{0}> You must be an administrator to change channel settings'.format(msg.author.id)
    else:
        m = '<@!{0}> You don\'t have permission'.format(msg.author.id)
    mymsg = yield from client.send_message(msg.channel,m)
    yield from asyncio.sleep(5)
    yield from client.delete_message(msg)
    yield from client.delete_message(mymsg)

def commandStatus(msg,settings):
    '<@!{0}> bot v{1} is online!'.format(msg.author.id,VERSION)


cmodules = [fortnite.FortniteModule(KEY_FNBR,KEY_TRACKERNETWORK),moderation.ModerationModule()]
defaultmodule = default.DefaultModule(cmodules,VERSION)

def close():
    asyncio.ensure_future(client.close())
client.loop.add_signal_handler(signal.SIGTERM,close)
client.loop.create_task(autoshop(KEY_FNBR))
client.loop.create_task(autostatus())
client.loop.create_task(autonews())
client.loop.create_task(handle_queue())
client.run(KEY_DISCORD)
