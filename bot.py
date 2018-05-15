import discord_wrapper as discord
import asyncio
import json
import os
import os.path
import sys
import signal
from datetime import datetime
import time
import traceback
import builtins
import logging
import logging.config

from modules import default, fortnite, moderation
from modules.module import Command
from dataretrieval import meta
from imagegeneration import shop
from datamanagement import sql
from utils import linecount

def getEnv(name,default=None):
    value = os.environ.get(name,None)
    if value == None:
        if default == None:
            value = input("Env variable not found, please enter {}: ".format(name))
        else:
            value = default
    return value

# constants
LINE_COUNT = linecount.count_project()

KEY_DISCORD = getEnv("KEY_DISCORD")
KEY_FNBR = getEnv("KEY_FNBR")
KEY_TRACKERNETWORK = getEnv("KEY_TRACKERNETWORK")
DATABASE_URL = getEnv("DATABASE_URL")
BOT_NAME = getEnv("BOT_NAME", "FortniteData")
TICKER_TIME = int(getEnv("TICKER_TIME", 30))
VERSION = {'name': BOT_NAME, 'version_name': '0.9.0', 'revison': getEnv('HEROKU_RELEASE_VERSION', 'v1'), 'description': getEnv('HEROKU_SLUG_DESCRIPTION', ''), 'lines': LINE_COUNT}
SHARD_NO = 0
SHARD_COUNT = 1
if len(sys.argv) > 2:
    try:
        SHARD_NO = int(sys.argv[1])
        SHARD_COUNT = int(sys.argv[2])
    except ValueError:
        pass

# functions
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


# setup logging
logging.config.fileConfig('logs/logger_conf.ini')


client = discord.Client(shard_id=SHARD_NO,shard_count=SHARD_COUNT)
client.queued_actions = []
client.database = sql.Database(url=DATABASE_URL)
builtins.client = client

@asyncio.coroutine
def autoshop(fnbr_key): # add fnbr not accessable fallback
    logger = logging.getLogger('autoshop')
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
                        bgs = server.get('backgrounds',{})
                        bgs_s = bgs.get('shop',[])
                        file = yield from shop.generate(shopdata,bgs_s,serverid)
                        content = "Data from <https://fnbr.co/>"
                        yield from client.send_file(discord.Object(server['channels']['autoshop']),file,content=content)
                        nextshoptime = round(time.mktime(rawtime.utctimetuple()) + (60*60*24))
                        client.database.set_server_info(serverid,next_shop=nextshoptime,latest_shop=file)
                    else:
                        logger.error('Error getting shop data %s: %s', str(shopdata.error), str(shopdata.json))
                        shopdata = None
        time_until_next = nextshop-now
        if time_until_next < 0:
            time_until_next = 1
        else:
            time_until_next += 60
        logger.info("Autoshop now:%d next:%d", now, nextshop)
        yield from asyncio.sleep(time_until_next)

@asyncio.coroutine
def autostatus():
    logger = logging.getLogger('autostatus')
    yield from client.wait_until_ready()
    while not client.is_closed:
        cache_raw = client.database.get_cache("status", once=True)
        if 'status' in cache_raw:
            cache = json.loads(cache_raw['status'])
        else:
            cache = {}
        data = meta.getStatus()
        changed = changes(cache,data)
        client.database.set_cache("status", json.dumps(data), once=True)
        servicechange = []
        for s in changed['services']:
            if changed['services'][s] is True:
                servicechange.append(s)
        embed = None
        if len(servicechange) > 0:
            embed = fortnite.StatusEmbed(data['online'],data['message'])
            for s in data['services']:
                embed.add_service(name=s,value=data['services'][s])
        elif changed['online'] == True or changed['message'] == True:
            embed = fortnite.StatusEmbed(data['online'],data['message'])
        if embed != None:
            for serverid in client.database.servers():
                server = client.database.server_info(serverid,channels=True)
                if 'autostatus' in server['channels']:
                    last_stats_msg = server.get('last_stats_msg', None)
                    last_stats_channel = server.get('last_stats_channel', None)
                    server = discord.Object(server['channels']['autostatus'])
                    if last_stats_msg is not None and last_stats_channel is not None:
                        old_message = discord.Object(last_stats_msg)
                        old_message.channel = discord.Object(last_stats_channel)
                        message = yield from client.edit_message(server, embed = embed)
                    else:
                        message = yield from client.send_message(server, embed = embed)
                    try:
                        sql.set_server_info(serverid, last_status_msg=message.id, last_status_channel=message.channel.id)
                    except:
                        error = traceback.format_exc()
                        logger.error('Error updating server info %s', error)
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
    logger = logging.getLogger('handle_queue')
    yield from client.wait_until_ready()
    while not client.is_closed:
        for queue_item in client.queued_actions:
            args = [client] + queue_item.args
            try:
                yield from queue_item.function(*args)
            except:
                pass
            client.queued_actions.remove(queue_item)
            logger.info('Handled queue action %s (%s), %s remain', str(queue_item.function), str(args), len(client.queued_actions))
        yield from asyncio.sleep(0.5)

@asyncio.coroutine
def ticker():
    ticker_text = ['Est. 2018 @mention for help','discord.me/fortniteroyale','Powering {user_count} users over {server_count} servers','{lines}... beep boop processing']
    yield from client.wait_until_ready()
    while not client.is_closed:
        for ticker in ticker_text:
            user_count = yield from count_users(client)
            ticker_f = ticker.format_map({'server_count':len(client.servers), 'lines': LINE_COUNT,'user_count': user_count})
            game = discord.Game(name=ticker_f,type=0)
            yield from client.change_presence(game=game)
            yield from asyncio.sleep(TICKER_TIME)


@asyncio.coroutine
def count_users(client_class):
    users = 0
    for server in client_class.servers:
        users += len(server.members)
    return users


@client.event
@asyncio.coroutine
def on_ready():
    logger = logging.getLogger()
    logger.info("Discord client logged in: %s %s", client.user.name, client.user.id)
    yield from client.edit_profile(username=BOT_NAME)
    yield from client.change_presence(game=discord.Game(name="Est. 2018 @mention for help",type=0),status="online",afk=False)
    defaultmodule.client_id = client.user.id


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
    if not msg.author.bot:
        if msg.content.startswith(prefix):
            command = msg.content[len(prefix):]
        else:
            command = None
        yield from commandHandler(command,msg)


@asyncio.coroutine
def commandHandler(command, msg):
    logger = logging.getLogger('commandHandler')
    if command != None:
        command = command.lower()
    serverid = msg.server.id
    serversettings = client.database.server_info(serverid,channels=True,backgrounds=True)
    if serversettings.get("server_name") != msg.server.name:
        client.database.set_server_info(serverid,server_name=msg.server.name)
    output = Command()
    output.delete_command = False
    if command != None:
        output = yield from defaultmodule._run(output,command,msg,serversettings)
        if output.empty:
            for i in range(0,len(cmodules)):
                output = yield from cmodules[i]._run(output,command,msg,serversettings)
        if output.empty:
            for i in range(0,len(cmodules)):
                output = yield from cmodules[i]._run_alias(output,command,msg,serversettings)
    else:
        output = yield from defaultmodule._run_alias(output,command,msg,serversettings)
        if output.empty:
            for i in range(0,len(cmodules)):
                output = yield from cmodules[i]._run_alias(output,command,msg,serversettings)
    if len(output.queue) > 0:
        client.queued_actions += output.queue
        logger.debug('Added queued action')
    if output.settings != None:
        if 'channels' in output.settings:
            for type in output.settings['channels']:
                client.database.set_server_channel(serverid,type,output.settings['channels'][type])
            output.settings.pop('channels')
        if 'backgrounds' in output.settings:
            backgrounds = output.settings.get('backgrounds')
            for type in backgrounds:
                client.database.set_server_backgrounds(serverid,backgrounds=backgrounds.get(type),type=type)
            output.settings.pop('backgrounds')
        client.database.set_server_info(serverid,**output.settings)
    if output.delete_command == True:
        yield from client.delete_message(msg)
    if output.typing == True:
        yield from client.send_typing(msg.channel)
    if output.noPermission != None:
        yield from noPermission(msg,output.noPermission,serversettings)
    if output.file != None:
        response = yield from client.send_file(msg.channel,output.file,content=output.content)
    elif output.embeds != None:
        for embed in output.embeds:
            response = yield from client.send_message(msg.channel,embed=embed)
    elif output.content != None or output.embed != None:
        try:
            response = yield from client.send_message(msg.channel,content=output.content,embed=output.embed)
        except discord.errors.HTTPException:
            logger.error(traceback.format_exc())
            if output.embed != None:
                logger.error('Error sending embed %s', json.dumps(output.embed.to_dict()))
            response = yield from client.send_message(msg.channel,content='Sorry there was an error sending response')
    if output.is_help == True:
        client.database.set_server_info(serverid,last_help_msg=response.id,last_help_channel=response.channel.id)
@asyncio.coroutine
def noPermission(msg,type,settings):
    serverid = msg.server.id
    if type == 'error':
        m = '<@!{0}> Sorry an error occured'
    elif type in settings['channels']:
        m = '<@!{0}> Please use the set {1} channel <#{2}>'.format(msg.author.id,type,settings['channels'][type])
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


cmodules = [fortnite.FortniteModule(KEY_FNBR, KEY_TRACKERNETWORK, client.database), moderation.ModerationModule()]
defaultmodule = default.DefaultModule(cmodules, VERSION)

def close():
    asyncio.ensure_future(client.close())
client.loop.add_signal_handler(signal.SIGTERM, close)
client.loop.create_task(autoshop(KEY_FNBR))
client.loop.create_task(autostatus())
client.loop.create_task(autonews())
client.loop.create_task(handle_queue())
client.loop.create_task(ticker())
client.run(KEY_DISCORD)
