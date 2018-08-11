import discord_wrapper as discord
import dbl
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

import localisation
from modules import default, fortnite, moderation, testing
from modules.module import Command
from dataretrieval import meta, cheatsheets
from imagegeneration import shop, upcoming
from datamanagement import sql
from utils import linecount
from utils.times import day_string as parse_second_time
from utils.times import tommorow
from time import time as now
from utils.discord import count_client_users, get_server_priority
from codemodules import modals

def getEnv(name,default=None):
    value = os.environ.get(name,None)
    if value == None:
        if default == None:
            value = input("Env variable not found, please enter {}: ".format(name))
        else:
            value = default
    return value

# constants
LINE_COUNT = 0

SENTRY_URL = getEnv('SENTRY_URL','')
KEY_DISCORD = getEnv("KEY_DISCORD")
KEY_FNBR = getEnv("KEY_FNBR")
KEY_TRACKERNETWORK = getEnv("KEY_TRACKERNETWORK")
KEY_DBL = getEnv("KEY_DBL",None)
DATABASE_URL = getEnv("DATABASE_URL")
BOT_NAME = getEnv("BOT_NAME", "RoyaleBot")
TICKER_TIME = int(getEnv("TICKER_TIME", 30))
DEFAULT_PREFIX = getEnv("DEFAULT_PREFIX",".rb ")
SHARD_NO = 0
SHARD_COUNT = 1
if len(sys.argv) > 2:
    try:
        SHARD_NO = int(sys.argv[1])
        SHARD_COUNT = int(sys.argv[2])
    except ValueError:
        pass
VERSION = {'name': BOT_NAME, 'version_name': '1.1.6', 'revison': getEnv('HEROKU_RELEASE_VERSION', 'v1'), 'description': getEnv('HEROKU_SLUG_DESCRIPTION', ''), 'lines': LINE_COUNT, 'shards': SHARD_COUNT}
RATE_LIMIT_TIME = 0.25

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
    prefix = settings.get('prefix',DEFAULT_PREFIX)
    if prefix == None:
        prefix = DEFAULT_PREFIX
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
logging_config = {
    'version': 1,
    'disable_existing_loggers': True,
     'formatters': {
        'verbose': {
            'format': '%(name)-12s %(levelname)-10s %(message)s'
        }
    },
    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'sentry': {
            'level':'ERROR',
            'class':'raven.handlers.logging.SentryHandler',
            'dsn':SENTRY_URL
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'sentry'],
    }
}
logging.config.dictConfig(logging_config)

localisation.loadLocales()
localisation.setDefault('en')

if SHARD_NO == 0:
    defaults_database = True
else:
    defaults_database = False

client = discord.Client(shard_id=SHARD_NO,shard_count=SHARD_COUNT)
client.queued_actions = []
client.database = sql.Database(False, url=DATABASE_URL)
builtins.client = client
modals.setup(client.send_message,client.edit_message,client.delete_message,client.add_reaction,client.clear_reactions)

@asyncio.coroutine
def debugger(function):
    logger = logging.getLogger('debugger')
    count = 0
    while not client.is_closed and count < 50:
        try:
            yield from function()
        except:
            error = traceback.format_exc()
            logger.error('Debugging error %s restarting...',error)
            count += 1

@asyncio.coroutine
def autoshop(): # add fnbr not accessable fallback
    logger = logging.getLogger('autoshop')
    yield from client.wait_until_ready()
    logger.info('Autoshop started')
    while not client.is_closed:
        servers = yield from get_server_priority(list(client.servers),client.database.get_priority_servers)
        needRestart = False
        for servers_r in servers:
            if needRestart:
                break
            for serverd in servers_r:
                serverid = serverd.id
                server = client.database.server_info(serverid,backgrounds=True,channels=True)
                if 'autoshop' in server['channels']:
                    locale = server.get('locale')
                    now = time.time()
                    nextshop = server.get('next_shop')
                    if nextshop is None:
                        nextshop = time.mktime(datetime.now().utctimetuple())
                    if now >= nextshop:
                        bgs = server.get('backgrounds',{})
                        bgs_s = bgs.get('shop',[])
                        try:
                            file = yield from shop.generate(KEY_FNBR,serverid,bgs_s)
                        except:
                            error = traceback.format_exc()
                            logger.error('Error generating image: %s',error)
                            needRestart = True
                            break
                        content = localisation.getMessage('autoshop',lang=locale)
                        nextshoptime = tommorow()
                        try:
                            yield from client.send_file(discord.Object(server['channels']['autoshop']),file,content=content)
                            client.database.set_server_info(serverid,next_shop=nextshoptime,latest_shop=file)
                        except (discord.errors.Forbidden, discord.errors.NotFound):
                            logger.info('Forbidden or not found on server: {}'.format(serverid))
                            serverdata = client.get_server(serverid)
                            if serverdata is None:
                                client.database.delete_server(serverid)
                            else:
                                try:
                                    client.database.set_server_info(serverid,next_shop=nextshoptime,latest_shop=file)
                                    client.database.set_server_channel(serverid,'autoshop',None)
                                except:
                                    error = traceback.format_exc()
                                    logger.error('Error updating database: {0}'.format(error))
                                try:
                                    text = localisation.getFormattedMessage('autoshop_no_access',channel=server['channels']['autoshop'],server_name=serverdata.name,lang=locale)
                                    yield from client.send_message(serverdata.owner,content=text)
                                except:
                                    error = traceback.format_exc()
                                    logger.error('Error sending message to owner: {0}'.format(error))
                        except:
                            error = traceback.format_exc()
                            logger.error('Error sending shop: %s', error)
                        yield from asyncio.sleep(RATE_LIMIT_TIME)
            time_until_next = nextshop-now
            if time_until_next < 0:
                time_until_next = 1
            else:
                time_until_next += 10
        logger.info("Autoshop now:%d next:%d updating in: %s", now, nextshop, parse_second_time(nextshop-now))
        yield from asyncio.sleep(time_until_next)

@asyncio.coroutine
def autostatus():
    logger = logging.getLogger('autostatus')
    yield from client.wait_until_ready()
    logger.info('Autostatus started')
    while not client.is_closed:
        update_time = now() + 120
        try:
            data = yield from meta.getStatus()
            logger.debug('Fetched status data (online: %s, services: %s)', data['online'], data['services'])
        except:
            error = traceback.format_exc()
            logger.error('Error getting server status: %s',error)
            yield from asyncio.sleep(5)
            continue
        try:
            embed = fortnite.StatusEmbed(data['online'],data['message'])
            for s in data['services']:
                embed.add_service(s,data['services'][s])
        except:
            error = traceback.format_exc()
            logger.error('Error compiling embed %s', error)
        logger.debug('Embed built')
        servers = yield from get_server_priority(list(client.servers),client.database.get_priority_servers)
        sent = []
        for servers_r in servers:
            for server_d in servers_r:
                serverid = server_d.id
                if serverid in sent:
                    continue
                else:
                    sent.append(serverid)
                try:
                    server = client.database.server_info(serverid,channels=True)
                except:
                    server = None

                if server is not None and 'autostatus' in server['channels']:
                    last_status_msg = server.get('last_status_msg', None)
                    last_status_channel = server.get('last_status_channel', None)
                    channel = discord.Object(server['channels']['autostatus'])
                    channel.server = discord.Object(serverid)
                    old_message = None
                    if last_status_msg is not None and last_status_channel is not None:
                        try:
                            old_message = yield from client.get_message(channel, last_status_msg)
                        except (discord.errors.NotFound, discord.errors.Forbidden):
                            old_message = None
                        except:
                            old_message = None
                            logger.error('Error getting message')
                    if serverid == '453193540118511619':
                        logger.debug('Update for team flarox')
                    if old_message is not None:
                        if old_message.channel.server.id != serverid:
                            logger.warning('Message from wrong server')
                        try:
                            message = yield from client.edit_message(old_message, embed = embed)
                        except:
                            error = traceback.format_exc()
                            logger.error('Error editing message %s', error)
                            message = None
                    else:
                        try:
                            message = yield from client.send_message(channel, embed = embed)
                        except:
                            error = traceback.format_exc()
                            logger.error('Error sending message %s', error)
                            message = None
                    if message is not None:
                        try:
                            client.database.set_server_info(serverid, last_status_msg=message.id, last_status_channel=message.channel.id)
                        except:
                            error = traceback.format_exc()
                            logger.error('Error updating server info %s', error)
                    yield from asyncio.sleep(RATE_LIMIT_TIME)
        next_time = update_time - now()
        logger.info('Autostatus update complete checking again in %s', parse_second_time(next_time))
        if next_time > 0:
            yield from asyncio.sleep(next_time)

@asyncio.coroutine
def autonews():
    logger = logging.getLogger('autonews')
    yield from client.wait_until_ready()
    logger.info('Autonews started')
    while not client.is_closed:
        update_time = 300
        cache = client.database.get_cache("news",once=False)
        if cache is None:
            cache = []
        data = meta.getNews('en')
        used = []
        embeds = []
        for msg in data['messages']:
            if not msg['title'] in cache:
                embeds.append(fortnite.NewsEmbed(msg,data['updated']))
                client.database.set_cache("news",msg['title'],once=False)
        servers = yield from get_server_priority(list(client.servers),client.database.get_priority_servers)
        for servers_r in servers:
            for serverd in servers_r:
                serverid = serverd.id
                server = client.database.server_info(serverid,channels=True)
                if 'autonews' in server['channels']:
                    for embed in embeds:
                        try:
                            yield from client.send_message(discord.Object(server['channels']['autonews']),embed=embed)
                        except:
                            error = traceback.format_exc()
                            logger.error('Unable to send news update: %s',error)
                    update_time -= RATE_LIMIT_TIME
                    yield from asyncio.sleep(RATE_LIMIT_TIME)
        logger.info('Auto news update complete checking again in %s', parse_second_time(update_time))
        if update_time > 0:
            yield from asyncio.sleep(update_time)

@asyncio.coroutine
def autocheatsheets():
    logger = logging.getLogger('autosheets')
    yield from client.wait_until_ready()
    logger.info('Autosheets started')
    while not client.is_closed:
        update_time = 600
        cache = client.database.get_cache('last_cheat_sheet',once=True)
        if cache is None:
            cache = {'season':0,'week':0}
        else:
            try:
                cache = json.loads(cache.get('last_cheat_sheet'))
            except:
                logger.debug(str(cache))
                cache = {'season':0,'week':0}
        old_cache = dict(cache)
        update = None
        data = yield from cheatsheets.get_cheat_sheets()
        for sheet in data:
            if ((sheet.season >= cache.get('season',0) and sheet.week > cache.get('week',0)) or sheet.season > cache.get('season',0)) and sheet.has_image:
                cache['season'] = sheet.season
                cache['week'] = sheet.week
                update = sheet
        if old_cache.get('season') != cache.get('season') or old_cache.get('week') != cache.get('week'):
            try:
                client.database.set_cache('last_cheat_sheet',json.dumps(cache),once=True)
                logger.info('Updated cache')
            except:
                error = traceback.format_exc()
                logger.error('Error updating cache: %s',error)
        else:
            logger.debug('%s\n%s',str(old_cache),str(cache))
        if update is not None:
            title = localisation.getFormattedMessage('autocheatsheets_title',season=update.season,week=update.week)
            description = localisation.getMessage('autocheatsheets_desc')
            embed = discord.Embed(title=title,description=description,color=0xe67e22)
            embed.set_image(url=update.image)
            logger.info('Embed built {0}.{1} image url: {2}'.format(update.season,update.week,update.image))
            servers = yield from get_server_priority(list(client.servers),client.database.get_priority_servers)
            for servers_r in servers:
                for serverd in servers_r:
                    serverid = serverd.id
                    server = client.database.server_info(serverid,channels=True)
                    if 'autocheatsheets' in server.get('channels',[]):
                        try:
                            yield from client.send_message(discord.Object(server['channels']['autocheatsheets']),embed=embed)
                        except:
                            error = traceback.format_exc()
                            logger.error('Unabled to send cheat sheet: %s',error)
                        update_time -= RATE_LIMIT_TIME
                        yield from asyncio.sleep(RATE_LIMIT_TIME)
        logger.info('Auto cheat sheets update complete checking again in %s', parse_second_time(update_time))
        if update_time > 0:
            yield from asyncio.sleep(update_time)

@asyncio.coroutine
def handle_queue():
    logger = logging.getLogger('handle_queue')
    yield from client.wait_until_ready()
    logger.info('Queue handler started')
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
    logger = logging.getLogger('ticker')
    ticker_text = ['Est. 2018 @mention for help','Powering {server_count} communities']
    yield from client.wait_until_ready()
    logger.info('Ticker started')
    while not client.is_closed:
        for ticker in ticker_text:
            ticker_f = ticker
            if ticker.find('{server_count}') >= 0:
                ticker_f = ticker_f.replace('{server_count}',str(len(client.servers)))
            if ticker.find('{user_count}') >= 0:
                users = yield from count_client_users(client,False)
                ticker_f = ticker_f.replace('{user_count}',str(users))
            game = discord.Game(name=ticker_f,type=0)
            yield from client.change_presence(game=game)
            yield from asyncio.sleep(TICKER_TIME)

@asyncio.coroutine
def dbl_api():
    logger = logging.getLogger('dbl_api')
    if KEY_DBL is not None:
        dbl_client = dbl.Client(client,KEY_DBL)
        logger.info('dbl updater started')
        yield from client.wait_until_ready()
        while not client.is_closed:
            sleeptime = 1800
            try:
                yield from dbl_client.post_server_count(client.shard_count,client.shard_id)
                logger.info('Posted server count to dbl')
            except dbl.errors.Forbidden:
                logger.warning('Forbidden to update server count')
                sleeptime = 30
            except:
                error = traceback.format_exc()
                logger.error('Error posting server count: {}'.format(error))
            yield from asyncio.sleep(sleeptime)
    else:
        logger.info('DBL api key not found')


@asyncio.coroutine
def server_deleter():
    logger = logging.getLogger('server_deleter')
    delete_time = 60*60*3
    yield from client.wait_until_ready()
    logger.info('Started')
    while not client.is_closed:
        last_seen = round(now())
        for server in client.servers:
            client.database.set_server_info(server.id,last_seen=last_seen)
        purge_ready = client.database.get_purge(last_seen-delete_time)
        for server in purge_ready:
            client.database.delete_server(server.get('server_id'))
        yield from asyncio.sleep(60*60)

@asyncio.coroutine
def pre_cache():
    logger = logging.getLogger('pre-cache')
    try:
        yield from shop.generate(KEY_FNBR,'',[])
        logger.info('Finished shop')
    except:
        error = traceback.format_exc()
        logger.error('Error precaching: %s',error)
    try:
        yield from upcoming.generate(KEY_FNBR,'',[])
        logger.info('Finished upcoming')
    except:
        error = traceback.format_exc()
        logger.error('Error precaching: %s',error)

@asyncio.coroutine
def count_users(client_class):
    users = 0
    for server in client_class.servers:
        users += len(server.members)
    return users


@client.event
@asyncio.coroutine
def on_reaction_add(reaction,user):
    yield from modals.reaction_handler(reaction,user)

@client.event
@asyncio.coroutine
def on_ready():
    logger = logging.getLogger()
    logger.info("Discord client logged in: %s %s %d/%d", client.user.name, client.user.id, client.shard_id, client.shard_count)
    yield from client.edit_profile(username=BOT_NAME)
    yield from client.change_presence(game=discord.Game(name="Est. 2018 @mention for help",type=0),status="online",afk=False)
    defaultmodule.client_id = client.user.id
    yield from pre_cache()


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
        prefix = DEFAULT_PREFIX
    else:
        prefix = settings.get("prefix")
        if prefix == None:
            prefix = DEFAULT_PREFIX
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
    if output.settings is not None:
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
    locale = settings.get('locale')
    serverid = msg.server.id
    if type == 'error':
        m = localisation.getFormattedMessage('error',author=msg.author.id,lang=locale)
    elif type in settings['channels']:
        m = localisation.getFormattedMessage('wrong_channel',author=msg.author.id,type=type,channel=settings['channels'][type],lang=locale)
    elif type == 'setchannel' or type == 'resetchannels':
        m = localisation.getFormattedMessage('channel_administrator',author=msg.author.id,lang=locale)
    else:
        m = localisation.getFormattedMessage('nopermission',author=msg.author.id,lang=locale)
    mymsg = yield from client.send_message(msg.channel,m)
    yield from asyncio.sleep(5)
    yield from client.delete_message(msg)
    yield from client.delete_message(mymsg)

def commandStatus(msg,settings):
    '<@!{0}> bot v{1} is online!'.format(msg.author.id,VERSION)


cmodules = [fortnite.FortniteModule(KEY_FNBR, KEY_TRACKERNETWORK, client.database), moderation.ModerationModule()]
defaultmodule = default.DefaultModule(cmodules, VERSION, database=client.database)

def close():
    asyncio.ensure_future(client.close())
client.loop.add_signal_handler(signal.SIGTERM, close)
# if SHARD_COUNT > 5:
#     if SHARD_NO == 0:
#         client.loop.create_task(autoshop())
#     elif SHARD_NO == 1:
#         client.loop.create_task(autostatus())
#     elif SHARD_NO == 2:
#         client.loop.create_task(autonews())
#     elif SHARD_NO == 3:
#         client.loop.create_task(handle_queue())
#     elif SHARD_NO == 4:
#         client.loop.create_task(ticker())
#     elif SHARD_NO == 5:
#         client.loop.create_task(dbl_api())
# else:
if shard_id == 0:
    client.loop.create_task(debugger(autoshop))
    client.loop.create_task(debugger(autostatus))
    client.loop.create_task(debugger(autonews))
    client.loop.create_task(debugger(autocheatsheets))
    client.loop.create_task(debugger(server_deleter))
    client.loop.create_task(handle_queue())
# client.loop.create_task(debugger(ticker))
# client.loop.create_task(dbl_api())
client.run(KEY_DISCORD)
