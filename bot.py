import discord
import asyncio
import json
import os.path
from datetime import datetime
import time
import traceback

from modules import default, fortnite, moderation
from modules.data import shop, meta

#constants
SETTINGSLOC = "settings.json"
VERSION = "0.0.6"

# file handlng
def readJson(fname):
    try:
        f = open(fname,"r")
        c = f.read()
        f.close()
    except FileNotFoundError:
        c = "{}"
    return json.loads(c)
def writeJson(fname,data={}):
    f = open(fname,"w")
    f.write(json.dumps(data))
    f.close()
def save(fname,data):
    writeJson(fname,data)
    return readJson(fname)
def settingsDefaults(): # setup default settings
    settings = readJson(SETTINGSLOC)
    if not 'prefix' in settings:
        settings['prefix'] = '!'
    if not 'bot_token' in settings:
        token = input("Enter your discord bot token (https://discordapp.com/developers/applications/me): ")
        settings['bot_token'] = token
    if not 'fnbr_key' in settings:
        key = input("Enter your fnbr api key (https://fnbr.co/api/docs): ")
        settings['fnbr_key'] = key
    if not 'tn_key' in settings:
        key = input("Enter your tn api key (https://fortnitetracker.com/site-api): ")
        settings['tn_key'] = key
    if not 'latest_shop' in settings:
        settings['last_shop'] = ''
    if not 'servers' in settings:
        settings['servers'] = {}
    save(SETTINGSLOC,settings)

def checkPermissions(channel,type,settings):
    try:
        if settings[type] == channel or settings[type] == '':
            p = True
        else:
            p = False
    except KeyError:
        p = False
    return p

def defaults(settings,serverid,msg,types=[]):
    # {'name':msg.channel.server.name,'shop':'','stats':'','autoshop':'','last_help':{'msg':'','channel':''},'backgrounds':[]}
    change = False
    if not serverid in settings['servers']:
        settings['servers'][serverid] = {}
    if not 'name' in settings['servers'][serverid]:
        settings['servers'][serverid]['name'] = msg.channel.server.name
        change = True
    elif settings['servers'][serverid]['name'] != msg.channel.server.name:
        settings['servers'][serverid]['name'] = msg.channel.server.name
        change = True
    if not 'channels' in settings['servers'][serverid]:
        settings['servers'][serverid]['channels'] = {}
        for type in types:
            settings['servers'][serverid]['channels'][type] = ''
        change = True
    for type in types:
        if not type in settings['servers'][serverid]['channels']:
            settings['servers'][serverid]['channels'][type] = ''
            change = True
    if not 'last_help' in settings['servers'][serverid]:
        settings['servers'][serverid]['last_help'] = {}
        change = True
    if not 'msg' in settings['servers'][serverid]['last_help']:
        settings['servers'][serverid]['last_help']['msg'] = ''
        change = True
    if not 'channel' in settings['servers'][serverid]['last_help']:
        settings['servers'][serverid]['last_help']['channel'] = ''
        change = True
    if not 'backgrounds' in settings['servers'][serverid]:
        settings['servers'][serverid]['backgrounds'] = ''
        change = True
    return settings, change

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


client = discord.Client()
client.queued_actions = []

@asyncio.coroutine
def autoshop(): # add fnbr not accessable fallback
    yield from client.wait_until_ready()
    while not client.is_closed:
        settings = readJson(SETTINGSLOC)
        shopdata = None
        for serverid in settings['servers']:
            server = settings['servers'][serverid]
            if 'autoshop' in server['channels'] and server['channels']['autoshop'] != '':
                now = time.time()
                nextshop = time.mktime(datetime.now().utctimetuple())
                if 'nextshop' in server:
                    nextshop = server['nextshop']
                if now >= nextshop:
                    if shopdata == None:
                        shopdata = shop.getShopData(settings['fnbr_key'])
                    rawtime = shop.getTime(shopdata.data.date)
                    file = shop.filename(rawtime)
                    if not os.path.isfile(file):
                        file = shop.generate(shopdata,server['backgrounds'])
                    content = "Data from <https://fnbr.co/>"
                    yield from client.send_file(discord.Object(server['channels']['autoshop']),file,content=content)
                    settings['servers'][serverid]['nextshop'] = time.mktime(rawtime.utctimetuple()) + (60*60*24)
                    settings['latest_shop'] = file
                    settings = save(SETTINGSLOC,settings)
        print("Autoshop now:{0} next:{1}".format(now,nextshop))
        yield from asyncio.sleep(60*15)

@asyncio.coroutine
def autostatus():
    yield from client.wait_until_ready()
    while not client.is_closed:
        settings = readJson(SETTINGSLOC)
        try:
            cache = settings['status_cache']
        except KeyError:
            cache = {}
        data = meta.getStatus()
        changed = changes(cache,data)
        cache = data
        settings['status_cache'] = cache
        settings = save(SETTINGSLOC,settings)
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
            for serverid in settings['servers']:
                server = settings['servers'][serverid]
                if server['channels']['autostatus'] != '':
                    yield from client.send_message(discord.Object(server['channels']['autostatus']),embed=embed)
        yield from asyncio.sleep(60*2)

@asyncio.coroutine
def autonews():
    yield from client.wait_until_ready()
    while not client.is_closed:
        settings = readJson(SETTINGSLOC)
        try:
            cache = settings['news_cache']
        except KeyError:
            cache = []
        data = meta.getNews('en')
        used = []
        embeds = []
        for msg in data['messages']:
            if not msg['title'] in cache:
                embeds.append(fortnite.NewsEmbed(msg,data['updated']))
        settings['news_cache'] = cache
        settings = save(SETTINGSLOC,settings)
        for serverid in settings['servers']:
            server = settings['servers'][serverid]
            if 'autonews' in server['channels']:
                if server['channels']['autonews'] != '':
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
    yield from client.edit_profile(username="FortniteData")
    yield from client.change_presence(game=discord.Game(name="Serving you since 2018 (!help)",type=0),status="online",afk=False)


@client.event
@asyncio.coroutine
def on_message(msg):
    settings = readJson(SETTINGSLOC)
    if not msg.author.bot and msg.content.startswith(settings['prefix']):
        command = msg.content[len(settings['prefix']):]
        yield from commandHandler(command,msg)
@client.event
@asyncio.coroutine
def on_message_edit(before,msg):
    settings = readJson(SETTINGSLOC)
    if not msg.author.bot and msg.content.startswith(settings['prefix']):
        command = msg.content[len(settings['prefix']):]
        yield from commandHandler(command,msg)

@asyncio.coroutine
def commandHandler(command,msg):
    command = command.lower()
    settings = readJson(SETTINGSLOC)
    serverid = msg.server.id
    settings,change = defaults(settings,serverid,msg,defaultmodule.types)
    if change:
        settings = save(SETTINGSLOC,settings)
    serversettings = settings['servers'][serverid]
    output = Command()
    admin = msg.author.server_permissions.administrator
    if command.startswith("setpresence"):
        if admin:
            yield from client.send_typing(msg.channel)
            output = SetPresence(msg,settings)
            yield from client.change_presence(game=output.game,status='online',afk=False)
        else:
            yield from noPermission(msg,None,settings)
    elif command.startswith("shutdown"):
        if msg.author.id == '293482190031945739':
            output = Shutdown(msg,settings)
        else:
            yield from noPermission(msg,None,settings)
    elif command.startswith("help"):
        if 'last_help' in serversettings and serversettings['last_help'] != {}:
            if 'msg' in serversettings['last_help'] and 'channel' in serversettings['last_help'] and serversettings['last_help']['msg'] != '' and serversettings['last_help']['channel'] != '':
                object = discord.Object(serversettings['last_help']['msg'])
                object.channel = discord.Object(serversettings['last_help']['channel'])
                try:
                    yield from client.delete_message(object)
                except:
                    pass
        if admin:
            output = defaultmodule.commands['adminhelp']
            output.run(msg,settings)
        else:
            output = defaultmodule.commands['help']
            output.run(msg,settings)
    else:
        output = defaultmodule.run(output,command,msg,settings)
        if output.content == None and output.embed == None and output.embeds == None:
            for i in range(0,len(cmodules)):
                output = cmodules[i]._run(output,command,msg,settings)
        if len(output.queue) > 0:
            client.queued_actions += output.queue
            print('Added queued action')
    settings = save(SETTINGSLOC,output.changeSettings(settings))
    if output.typing == True:
        yield from client.send_typing(msg.channel)
    if output.noPermission != None:
        yield from noPermission(msg,output.noPermission,settings)
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
        settings['servers'][serverid]['last_help'] = {'msg':response.id,'channel':response.channel.id}
        settings = save(SETTINGSLOC,settings)
    if output.shutdown == True:
        yield from client.close()
@asyncio.coroutine
def noPermission(msg,type,settings):
    serverid = msg.server.id
    if type == 'shop' or type == 'stats':
        m = '<@!{0}> Please use the set {1} channel <#{2}>'.format(msg.author.id,type,settings['servers'][serverid]['channels']['shop'])
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


settingsDefaults()
settings = readJson(SETTINGSLOC)

cmodules = [fortnite.FortniteModule(),moderation.ModerationModule()]
defaultmodule = default.DefaultModule(cmodules,VERSION)
client.loop.create_task(autoshop())
client.loop.create_task(autostatus())
client.loop.create_task(autonews())
client.loop.create_task(handle_queue())
client.run(settings['bot_token'])
