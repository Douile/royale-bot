import discord
import asyncio
import json
import traceback
import logging
import logging.config

import localisation
from modules import default, fortnite, moderation, testing
from modules.module import Command
from data import meta, cheatsheets
from images import shop, upcoming
from utils import getEnv, dispatcher, sql, modals
from utils.times import day_string as parse_second_time, tommorow as tommorow_time, now as now_time
from utils.discord import count_client_users, get_server_priority

# constants
KEY_DISCORD = getEnv("KEY_DISCORD")
KEY_FNBR = getEnv("KEY_FNBR")
KEY_TRACKERNETWORK = getEnv("KEY_TRACKERNETWORK")
DATABASE_URL = getEnv("DATABASE_URL")
BOT_NAME = getEnv("BOT_NAME", "RoyaleBot")
TICKER_TIME = int(getEnv("TICKER_TIME", 30))
DEFAULT_PREFIX = getEnv("DEFAULT_PREFIX",".rb ")
VERSION = {'name': BOT_NAME, 'version_name': '1.1.6', 'revison': getEnv('HEROKU_RELEASE_VERSION', 'v1'), 'description': getEnv('HEROKU_SLUG_DESCRIPTION', '')}
RATE_LIMIT_TIME = 0.25
DEBUG_CRASH_ALLOWED = 2

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
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    }
}
logging.config.dictConfig(logging_config)

localisation.loadLocales()
localisation.setDefault('en')

@asyncio.coroutine
def debugger(client,function):
    logger = logging.getLogger('debugger')
    count = 0
    while not client.is_closed and count < DEBUG_CRASH_ALLOWED:
        try:
            yield from function(client)
        except:
            error = traceback.format_exc()
            logger.error('Debugging error %s restarting...',error)
            count += 1


@asyncio.coroutine
def autoshop(client): # add fnbr not accessable fallback
    # errors with timing (repeated) - possibly timezones
    logger = logging.getLogger('autoshop')
    logger.info('Autoshop updating')
    servers = yield from get_server_priority(list(client.servers),client.database.get_priority_servers)
    # needRestart = False
    for servers_r in servers:
        # if needRestart:
        #     break
        for serverd in servers_r:
            serverid = serverd.id
            server = client.database.server_info(serverid,backgrounds=True,channels=True)
            if 'autoshop' in server['channels']:
                locale = server.get('locale')
                bgs = server.get('backgrounds',{})
                bgs_s = bgs.get('shop',[])
                try:
                    file = yield from shop.generate(KEY_FNBR,serverid,bgs_s)
                except:
                    error = traceback.format_exc()
                    logger.error('Error generating image: %s',error)
                    # needRestart = True
                    # break
                    continue
                content = localisation.getMessage('autoshop',lang=locale)
                # nextshoptime = tommorow_time()
                try:
                    yield from client.send_file(discord.Object(server['channels']['autoshop']),file,content=content)
                    # client.database.set_server_info(serverid,next_shop=nextshoptime,latest_shop=file)
                except (discord.errors.Forbidden, discord.errors.NotFound):
                    logger.info('Forbidden or not found on server: {}'.format(serverid))
                    serverdata = client.get_server(serverid)
                    # delete server check make this seperate function (repeated in automated tasks)
                    if serverdata is None:
                        client.database.delete_server(serverid)
                    else:
                        try:
                            # client.database.set_server_info(serverid,next_shop=nextshoptime,latest_shop=file)
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
    logger.info("Autoshop update complete")
    return 0


@asyncio.coroutine
def autostatus(client):
    logger = logging.getLogger('autostatus')
    logger.info('Autostatus updating')
    try:
        data = yield from meta.getStatus()
        logger.debug('Fetched status data (online: %s, services: %s)', data['online'], data['services'])
    except:
        error = traceback.format_exc()
        logger.error('Error getting server status: %s',error)
        return 1
    try:
        embed = fortnite.StatusEmbed(data['online'],data['message'])
        for s in data['services']:
            embed.add_service(s,data['services'][s])
    except:
        error = traceback.format_exc()
        logger.error('Error compiling embed %s', error)
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
                    except discord.errors.NotFound:
                        client.database.set_server_channel(serverid, 'autocheatsheets', None)
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
    logger.info('Autostatus update done')
    return 0


@asyncio.coroutine
def autonews(client):
    logger = logging.getLogger('autonews')
    logger.info('Autonews updating')
    cache = client.database.get_cache("news",once=False)
    if cache is None:
        cache = []
    data = yield from meta.getNews('en')
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
    logger.info('Auto news update complete')
    return 0


@asyncio.coroutine
def autocheatsheets(client):
    logger = logging.getLogger('autosheets')
    logger.info('Autosheets started')
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
        logger.debug('%s -> %s',str(old_cache),str(cache))
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
    logger.info('Autocheatsheets update complete')
    return 0

@asyncio.coroutine
def handle_queue(client):
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
def commandHandler(client, command, msg, serversettings):
    logger = logging.getLogger('commandHandler')
    if command != None:
        command = command.lower()
    serverid = msg.server.id
    if serversettings.get("server_name") != msg.server.name:
        client.database.set_server_info(serverid,server_name=msg.server.name)
    output = Command()
    output.delete_command = False
    if command != None:
        output = yield from client.defaultmodule._run(client,output,command,msg,serversettings)
        if output.empty:
            for i in range(0,len(client.cmodules)):
                output = yield from client.cmodules[i]._run(client,output,command,msg,serversettings)
        if output.empty:
            for i in range(0,len(client.cmodules)):
                output = yield from client.cmodules[i]._run_alias(client,output,command,msg,serversettings)
    else:
        output = yield from client.defaultmodule._run_alias(client,output,command,msg,serversettings)
        if output.empty:
            for i in range(0,len(client.cmodules)):
                output = yield from client.cmodules[i]._run_alias(client,output,command,msg,serversettings)
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
        yield from noPermission(client, msg,output.noPermission,serversettings)
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
def noPermission(client, msg,type,settings):
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

class Bot(discord.Client):
    def __init__(self,*,id=0,count=1,input=None,output=None):
        super().__init__(shard_id=id,shard_count=count,loop=asyncio.new_event_loop(),max_messages=100)
        self.queued_actions = []
        self.input = input
        self.output = output
        self.database = sql.Database(False, url=DATABASE_URL)

    @asyncio.coroutine
    def on_reaction_add(self, reaction,user):
        yield from modals.reaction_handler(reaction,user)

    @asyncio.coroutine
    def on_ready(self):
        logger = logging.getLogger()
        logger.info("Discord client logged in: %s (%s) Shard:%d/%d", self.user.name, self.user.id, self.shard_id, self.shard_count)
        logger.info("Invite url: %s", discord.utils.oauth_url(self.user.id,permissions=discord.Permissions(administrator=True)))
        yield from self.change_presence(game=discord.Game(name="Est. 2018 @mention for help",type=0),status="online",afk=False)
        self.defaultmodule.client_id = self.user.id

    @asyncio.coroutine
    def on_message(self, msg):
        if msg.server is None:
            return None
        settings = self.database.server_info(msg.server.id,channels=True,backgrounds=True)
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
            yield from commandHandler(self, command,msg,settings)

    def run(self):
        self.cmodules = [fortnite.FortniteModule(KEY_FNBR, KEY_TRACKERNETWORK, self.database), moderation.ModerationModule()]
        self.defaultmodule = default.DefaultModule(self.cmodules, VERSION, database=self.database)
        # create cron like scheduler?
        # 1 loop that dispatches these auto tasks, kills + restarts if take to long/freeze
        # self.loop.create_task(debugger(self,autostatus))
        # self.loop.create_task(debugger(self,autonews))
        # self.loop.create_task(debugger(self,autocheatsheets))
        # self.loop.create_task(debugger(self,autoshop))
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.register(autostatus,pass_client=True,hours=None,minutes=dispatcher.Times.MINS_2)
        self.dispatcher.register(autonews,pass_client=True,hours=None,minutes=dispatcher.Times.MINS_5)
        self.dispatcher.register(autocheatsheets,pass_client=True,hours=None,minutes=dispatcher.Times.MINS_10)
        self.dispatcher.register(autoshop,pass_client=True,hours=0,minutes=2)
        self.loop.create_task(debugger(self,self.dispatcher.run))
        # help deletes aren't working because queue handler is never registered
        super().run(KEY_DISCORD)


if __name__ == '__main__':
    bot = Bot()
    bot.run()
