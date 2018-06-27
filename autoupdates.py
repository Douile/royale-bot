import discord_wrapper as discord
import dbl
import asyncio
import logging
import logging.config
import os

from dataretrieval import meta
from imagegeneration import shop
from datamanagement import sql
from utils.times import day_string as parse_second_time

def getEnv(name,default=None):
    value = os.environ.get(name,None)
    if value == None:
        if default == None:
            value = input("Env variable not found, please enter {}: ".format(name))
        else:
            value = default
    return value

# constants
SENTRY_URL = getEnv('SENTRY_URL','')
KEY_DISCORD = getEnv("KEY_DISCORD")
KEY_FNBR = getEnv("KEY_FNBR")
KEY_TRACKERNETWORK = getEnv("KEY_TRACKERNETWORK")
KEY_DBL = getEnv("KEY_DBL",None)
DATABASE_URL = getEnv("DATABASE_URL")

# logging
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
            'level':'WARNING',
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

client = discord.Client()
client.database = sql.Database(False, url=DATABASE_URL)

@asyncio.coroutine
def autoshop(): # add fnbr not accessable fallback
    logger = logging.getLogger('autoshop')
    yield from client.wait_until_ready()
    vote_link = 'https://discordbots.org/bot/{0}/vote'.format(client.user.id)
    logger.info('Autoshop started')
    while not client.is_closed:
        shopdata = None
        servers = client.servers
        for serverd in list(servers):
            serverid = serverd.id
            server = client.database.server_info(serverid,backgrounds=True,channels=True)
            if 'autoshop' in server['channels']:
                now = time.time()
                if 'next_shop' in server:
                    nextshop = server['next_shop']
                if nextshop == None:
                    nextshop = time.mktime(datetime.now().utctimetuple())
                if now >= nextshop:
                    if shopdata == None:
                        shopdata = yield from shop.getShopData(KEY_FNBR)
                    if shopdata.type == 'shop':
                        rawtime = shop.getTime(shopdata.data.date)
                        bgs = server.get('backgrounds',{})
                        bgs_s = bgs.get('shop',[])
                        try:
                            file = yield from shop.generate(KEY_FNBR,serverid,bgs_s)
                        except:
                            error = traceback.format_exc()
                            logger.error('Error generating image: %s',error)
                            continue
                        content = "Data from <https://fnbr.co/>\nVote for this bot here: <{0}>".format(vote_link)
                        nextshoptime = round(time.mktime(rawtime.utctimetuple()) + (60*60*24))
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
                                    yield from client.send_message(serverob.owner,content='I was unable to access the autoshop channel you set in your server `{0}`. I have deleted the channel from my database.'.format(serverob.name))
                                except:
                                    error = traceback.format_exc()
                                    logger.error('Error sending message to owner: {0}'.format(error))
                        except:
                            error = traceback.format_exc()
                            logger.error('Error sending shop: %s', error)
                        yield from asyncio.sleep(RATE_LIMIT_TIME)
                    else:
                        logger.error('Error getting shop data %s: %s', str(shopdata.error), str(shopdata.json))
                        shopdata = None
        time_until_next = nextshop-now
        if time_until_next < 0:
            time_until_next = 1
        else:
            time_until_next += 60
        logger.info("Autoshop now:%d next:%d updating in: %s", now, nextshop, parse_second_time(nextshop-now))
        yield from asyncio.sleep(time_until_next)

@asyncio.coroutine
def autostatus():
    logger = logging.getLogger('autostatus')
    yield from client.wait_until_ready()
    logger.info('Autostatus started')
    while not client.is_closed:
        update_time = 120
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
        servers = client.servers
        for server_d in list(servers):
            serverid = server_d.id
            server = client.database.server_info(serverid,channels=True)
            if 'autostatus' in server['channels']:
                last_status_msg = server.get('last_status_msg', None)
                last_status_channel = server.get('last_status_channel', None)
                server = discord.Object(server['channels']['autostatus'])
                old_message = None
                if last_status_msg is not None and last_status_channel is not None:
                    channel = discord.Object(last_status_channel)
                    try:
                        old_message = yield from client.get_message(channel, last_status_msg)
                    except (discord.errors.NotFound, discord.errors.Forbidden):
                        old_message = None
                    except:
                        old_message = None
                        logger.error('Error getting message')

                if old_message is not None:
                    try:
                        message = yield from client.edit_message(old_message, embed = embed)
                    except:
                        error = traceback.format_exc()
                        logger.error('Error editing message %s', error)
                else:
                    try:
                        message = yield from client.send_message(server, embed = embed)
                    except:
                        error = traceback.format_exc()
                        logger.error('Error sending message %s', error)
                try:
                    client.database.set_server_info(serverid, last_status_msg=message.id, last_status_channel=message.channel.id)
                except:
                    error = traceback.format_exc()
                    logger.error('Error updating server info %s', error)
                update_time -= RATE_LIMIT_TIME
                yield from asyncio.sleep(RATE_LIMIT_TIME)
        logger.info('Autostatus update complete checking again in %s', parse_second_time(update_time))
        if update_time > 0:
            yield from asyncio.sleep(update_time)

@asyncio.coroutine
def autonews():
    logger = logging.getLogger('autonews')
    yield from client.wait_until_ready()
    logger.info('Autonews started')
    while not client.is_closed:
        update_time = 300
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
        servers = client.servers
        for serverd in list(servers):
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
def restarter(function):
    logger = logging.getLogger('restarter')
    while 1:
        try:
            yield from function()
        except:
            error = traceback.format_exc()
            logger.error('Error %s restarting...',error)

client.loop.create_task(restarter(autoshop))
client.loop.create_task(restarter(autostatus))
client.loop.create_task(autonews())
client.run(KEY_DISCORD)
