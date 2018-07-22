from .module import Module, Command, parse_user_at
from dataretrieval import aiofnotes, meta
from imagegeneration import shop, stats, upcoming
from utils import strings, arrays
import localisation
import traceback
from datetime import datetime
import discord
import asyncio
import urllib
import logging

logger = logging.getLogger('bot.fortnite')

class FortniteModule(Module):
    def __init__(self,fnbr_key='',tn_key='',sql=None):
        super().__init__(name="Fortnite",description="Commands related to fortnite",category="fortnite")
        self.commands = {
            'shop': Shop(fnbr_key),
            'stats': Stats(tn_key,sql),
            'upcoming': Upcoming(fnbr_key),
            'setbackground': SetBackgrounds(),
            'news': News(),
            'status': Servers(),
            #'patchnotes': PatchNotes(),
            'link': Link(sql),
            'unlink': UnLink(sql),
            'resetstatus': ResetStatus()
        }
        self.types = ['autoshop','autostatus','autonews','autocheatsheets']
        for command_name in self.commands:
            command = self.commands[command_name]
            if command.permission is not None and not command.permission in self.types and command.permission != 'admin':
                self.types.append(command.permission)
class Shop(Command):
    def __init__(self,fnbr_key):
        super().__init__(name="shop",description=localisation.PreMessage('shop_help'))
        self.permission = 'shop'
        self.fnbr_key = fnbr_key
    @asyncio.coroutine
    def run(self,command,msg,settings):
        logger = logging.getLogger('shop-command')
        try:
            # shopdata = yield from shop.getShopData(self.fnbr_key)
            # if shopdata.status == 200:
            #     bgs = settings.get('backgrounds',{})
            #     bgs_s = bgs.get('shop',[])
            #     logger.debug('Generating shop')
            #     file = yield from shop.generate(shopdata,bgs_s,msg.server.id)
            #     self.typing = True
            #     self.file = file
            #     self.content = "Data from <https://fnbr.co>"
            #     self.settings = {'latest_shop': file}
            # else:
            #     self.content = "Sorry there was an api error: {0}. All data from <https://fnbr.co>".format(shopdata.status)
            #     if 'latest_shop' in settings and settings['latest_shop'] != '':
            #         self.file = settings['latest_shop']
            logger.debug('Generating')
            bgs = settings.get('backgrounds',{})
            bgs_s = bgs.get('shop',[])
            file = yield from shop.generate(self.fnbr_key,msg.server.id,bgs_s)
            self.typing = True
            self.file = file
            self.content = localisation.getMessage('shop_success')
        except Exception as e:
            self.content = localisation.getMessage('shop_error')
            logger.error(traceback.format_exc())
class Upcoming(Command):
    def __init__(self,fnbr_key):
        super().__init__(name="upcoming",description=localisation.PreMessage('upcoming_help'),permission='upcoming')
        self.fnbr_key = fnbr_key
    @asyncio.coroutine
    def run(self,command,msg,settings):
        logger = logging.getLogger('upcomming-command')
        try:
            # data = yield from upcoming.getData(self.fnbr_key)
            # if data.status == 200:
            #     bgs = settings.get('backgrounds',{})
            #     bgs_s = bgs.get('shop',[])
            #     logger.debug('Generating shop')
            #     file = yield from upcoming.generate(data,bgs_s,msg.server.id)
            #     self.typing = True
            #     self.file = file
            #     self.content = "Data from <https://fnbr.co>"
            # else:
            #     self.content = "Sorry there was an api error: {0}. All data from <https://fnbr.co>".format(shopdata.status)
            logger.debug('Generating')
            bgs = settings.get('backgrounds',{})
            bgs_s = bgs.get('upcoming',[])
            file = yield from upcoming.generate(self.fnbr_key,msg.server.id,bgs_s)
            self.typing = True
            self.file = file
            self.content = localisation.getMessage('shop_success')
        except Exception as e:
            self.content = localisation.getMessage('shop_error')
            logger.error(traceback.format_exc())

class Stats(Command):
    def __init__(self,tn_key,sql):
        super().__init__(name='stats',description=localisation.PreMessage('stats_help'),permission='stats',aliases=['{prefix}'])
        self.tn_key = tn_key
        self.sql = sql
    @asyncio.coroutine
    def run(self,command,msg,settings):
        logger = logging.getLogger('stats')
        if command.startswith('stats'):
            args = command[len('stats'):].strip()
        else:
            args = command.strip()
        type = 'regular'
        match = strings.startmatches(args, ['cs','currentseason'])
        if match is not None:
            args = args[len(match):].strip()
            type = 'curr_season'
        user = yield from parse_fortnite_user(args, msg.author.id, msg.server.id, self.sql)
        name = user.get('name')
        platform = user.get('platform')
        linked = user.get('linked')
        if len(name.strip()) > 0:
            try:
                logger.debug('Stats command name: %s platform %s', name, platform)
                bgs = settings.get('backgrounds',{})
                bgs_s = bgs.get('stat',[])
                if type == 'regular':
                    statsimage = yield from stats.generate(self.tn_key,name,platform,bgs_s)
                elif type == 'curr_season':
                    statsimage = yield from stats.generate_season(self.tn_key,name,platform,bgs_s)
                if statsimage is None:
                    if linked:
                        self.content = localisation.getFormattedMessage('stats_notfound_link',username=name,platform=platform)
                    else:
                        self.content = localisation.getFormattedMessage('stats_notfound',username=name,platform=platform)
                        if platform != 'pc':
                            self.content += localisation.getMessage('stats_notfound_console')
                else:
                    self.typing = True
                    statsimage.save('generatedstats.png')
                    self.content = '<https://{}>'.format(urllib.parse.quote('fortnitetracker.com/profile/{1}/{0}'.format(name,platform)))
                    self.file = 'generatedstats.png'
            except Exception as e:
                if linked:
                    self.content = localisation.getFormattedMessage('stats_error_link',username=name,platform=platform)
                else:
                    self.content = localisation.getFormattedMessage('stats_error',username=name,platform=platform)
                logger.error(traceback.format_exc())
        else:
            if linked:
                self.content = localisation.getFormattedMessage('stats_short_link',username=name,platform=platform)
            else:
                self.content = localisation.getFormattedMessage('stats_short',author=msg.author.id)
        if name.find('shop') > -1 or name.find('help') > -1 or name.find('setprefix') > -1:
            self.content += localisation.getMessage('stats_command')
class Matches(Command):
    def __init__(self,tn_key,sql):
        super().__init__(name='matches',permission='stats')
        self.tn_key = tn_key
        self.sql = sql
    @asyncio.coroutine
    def run(self,command,msg,settings):
        logger = logging.getLogger('matches')
        if command.startswith('matches'):
            args = command[len('matches'):].strip()
        else:
            args = command.strip()
        user = yield from parse_fortnite_user(args, msg.author.id, msg.server.id, self.sql)
        name = user.get('name')
        platform = user.get('platform')
        try:
            logger.debug('Stats command name: %s platform %s', name, platform)
            bgs = settings.get('backgrounds',{})
            bgs_s = bgs.get('stat',[])
            statsimage = yield from stats.generate_performance(self.tn_key,name,platform,bgs_s)
            if statsimage == None:
                self.content = '<@!{author}> User not found'
            else:
                self.typing = True
                statsimage.save('generatedmatches.png')
                self.file = 'generatedmatches.png'
        except Exception as e:
            self.content = "Error getting stats"
            logger.error(traceback.format_exc())

class Link(Command):
    def __init__(self,sql):
        super().__init__(name='link',description=localisation.PreMessage('link_help'),permission='stats')
        self.sql = sql
    @asyncio.coroutine
    def run(self,command,msg,settings):
        command_size = len('link ')
        if len(command) > command_size:
            user = yield from parse_fortnite_user(command[command_size:])
            name = user.get('name')
            platform = user.get('platform')
            if len(name.strip()) > 0:
                self.content = localisation.getFormattedMessage('link_success',author=msg.author.id,username=name,platform=platform)
                try:
                    self.sql.set_link(msg.author.id,name,platform)
                except:
                    traceback.print_exc()
                    self.content = localisation.getFormattedMessage('link_error',author=msg.author.id)
            else:
                self.content = localisation.getFormattedMessage('link_short',author=msg.author.id)
        else:
            self.content = localisation.getFormattedMessage('link_short',author=msg.author.id)
class UnLink(Command):
    def __init__(self,sql):
        super().__init__(name='unlink',description=localisation.PreMessage('unlink_help'),permission='stats')
        self.sql = sql
    @asyncio.coroutine
    def run(self,command,msg,settings):
        try:
            self.sql.delete_link(msg.author.id)
            self.content = localisation.getFormattedMessage('unlink_success',author=msg.author.id)
        except:
            traceback.print_exc()
            self.content = localisation.getFormattedMessage('unlink_error',author=msg.author.id)
class SetBackgrounds(Command):
    def __init__(self):
        self.background_types = ['shop','stat','upcoming']
        super().__init__(name='setbackground',description=localisation.PreMessage('setbackground_help',types=arrays.message_string(self.background_types)))
        self.permission = 'admin'
    @asyncio.coroutine
    def run(self,command,msg,settings):
        locale = settings.get('locale')
        urls = command.split(" ")
        type = None
        if len(urls) < 2:
            backgrounds = []
        else:
            if urls[1].lower() in self.background_types:
                type = urls[1].lower()
                backgrounds = urls[2:]
            else:
                backgrounds = urls[1:]
        if type is not None:
            self.settings = {'backgrounds': {type:backgrounds}}
            self.content = localisation.getFormattedMessage('setbackground_success',author=msg.author.id,type=type,lang=locale)
        else:
            self.content = localisation.getFormattedMessage('setbackground_error',author=msg.author.id,types=arrays.message_string(self.background_types),lang=locale)
class News(Command):
    def __init__(self):
        super().__init__(name='news',description=localisation.PreMessage('news_help'))
        self.permission = 'news'
    @asyncio.coroutine
    def run(self,command,msg,settings):
        lang = 'en'
        news = meta.getNews(lang)
        if news['success']:
            self.embeds = []
            for msg in news['messages']:
                embed = NewsEmbed(msg,news['updated'])
                self.embeds.append(embed)
        else:
            self.content = localisation.getFormattedMessage('news_error',author=msg.author.id)
class Servers(Command):
    def __init__(self):
        super().__init__(name='status',description=localisation.PreMessage('status_help'),permission='status')
    @asyncio.coroutine
    def run(self,command,msg,settings):
        try:
            status = yield from meta.getStatus()
            self.content = localisation.getFormattedMessage('servers_success',author=msg.author.id)
            self.embed = StatusEmbed(status['online'],status['message'])
            for s in status['services']:
                self.embed.add_service(name=s,value=status['services'][s])
        except:
            self.content = localisation.getFormattedMessage('servers_error',author=msg.author.id)

class PatchNotes(Command):
    def __init__(self):
        super().__init__(name='patchnotes',description="Get the latest patchnotes. `{prefix}patchnotes ([d], [detail])` include `d` or `detail` for a more detailed breakdown of the patchnotes.", permission='patchnotes')
    @asyncio.coroutine
    def run(self,command,msg,settings):
        args = command.split(" ")
        try:
            arg = args[1].lower()
        except IndexError:
            arg = ''
        if arg == 'd' or arg == 'detail':
            detailed = True
        else:
            detailed = False
        notes = yield from aiofnotes.fetch_patch_notes(1, 0, detailed)
        logger.debug('Fetched patch notes: %s', notes)
        if notes['success']:
            if arg == 't':
                self.content = PatchNotesText(notes['notes'][0])
            else:
                self.embed = PatchNotesEmbed(notes['notes'][0])
                if notes['notes'][0]['simple'] != None:
                    self.content = notes['notes'][0]['simple']['video']
        else:
            self.content = 'Sorry <@!{author}> we were unable to get the patch notes'

class ResetStatus(Command):
    def __init__(self):
        super().__init__(name='resetstatus',description=localisation.PreMessage('resetstatus_help'),permission='admin')
    @asyncio.coroutine
    def run(self,command,msg,settings):
        self.content = 'Reseting your autostatus, a new message will be delivered on the next update (every 2 mins)'
        self.settings = {'last_status_msg':None,'last_status_channel':None}

class ShopEmbed(discord.Embed):
    def __init__(self,date,filename):
        super().__init__(title=date)
        fileurl = 'attachment://{}'.format(filename)
        self.set_image(url=fileurl)
class StatusEmbed(discord.Embed):
    def __init__(self,online=False,message=''):
        if online == True:
            color = 0x00ff00
            title = 'Fortnite servers are online'
            footer = '✔️'
        else:
            color = 0xff0000
            title = 'Fortnite servers are down'
            footer = '❌'
        super().__init__(title=title,color=color,timestamp=datetime.utcnow())
        self.set_footer(text=footer)
        if online == False:
            self.description = message
        else:
            self.description = '_ _'
        self.url = meta.STATUS_SERVICES
    def add_service(self,name='',value=''):
        level = -1
        if value == 'Operational':
            level = 0
        elif value == 'Major Outage':
            level = 2
        else:
            level = 1
        if level == 2:
            value = ':x: __**{0}**__'.format(value)
            self.color = 0xff0000
        elif level == 1:
            value = ':x: **{0}**'.format(value)
            if self.color != 0xff0000:
                self.color = 0xFFA700
        else:
            value = ':white_check_mark: {0}'.format(value)
        if level > 0:
            self.set_footer(text='❌')
        self.add_field(name=name,value=value,inline=False)
class NewsEmbed(discord.Embed):
    def __init__(self,message,timestamp):
        super().__init__(title=message['title'],description=message['body'],color=0x761fa1,timestamp=shop.getTime(timestamp))
        if 'image' in message:
            self.set_thumbnail(url=message['image'])
class PatchNotesEmbed(discord.Embed):
    def __init__(self,note):
        super().__init__(description=note['short'],color=0x761fa1,timestamp=shop.getTime(note['date']),url=note['url'])
        self.set_image(url=note['image'])
        self.set_author(name=note['title'],url=note['url'])
        self.set_footer(text=note['author'])
        if note['detailed'] != None:
            for detail in note['detailed']:
                if detail['value'].strip() == '':
                    self.add_field(name=detail['title'][:256],value='[NOT SET]',inline=False)
                elif len(detail['value']) > 1024:
                    title = detail['title']
                    value = detail['value']
                    while value != '':
                        v = value[:1024]
                        value = value[1024:]
                        self.add_field(name=title[:256],value=v,inline=False)
                        title = detail['title'][:256-12] +' (continued)'
                else:
                    self.add_field(name=detail['title'][:256],value=detail['value'],inline=False)
        if note['simple'] != None:
            self.description = note['simple']['description']
            for extra in note['simple']['extra']:
                self.add_field(name=extra['title'],value=extra['value'],inline=False)
class PatchNotesText:
    def __init__(self, note):
        data = note['simple']
        self.content = '***Patch Notes v{version}***\n**{short}**'
        map = {
            'version': note['title'],
            'short': note['shorts']
        }
        self.content.format_map(map)
    def __str__(self):
        return self.content
class StatsEmbed(discord.Embed):
    def __init__(self, data):
        if data.get('status') == 200:
            name = data.get('epicUserHandle','Not found')
            desc = "{0} player".format(data.get('platformNameLong','UNKNOWN'))
            color = 0x00ff00
        else:
            name = 'Network error'
            desc = '{0} {1}'.format(data.get('status'),data.get('error'))
            color = 0xff0000
        super().__init__(title=name,description=desc,color=color)
        lifetime = data.get('lifeTimeStats',None)
        if lifetime != None:
            for stat in lifetime:
                key = stat.get('key')
                value = stat.get('value')
                self.add_field(name=key,value=value,inline=False)

@asyncio.coroutine
def parse_fortnite_user(args, author=None, server=None, sql=None):
    linked = False
    try:
        s = args.index(' ')
        platform = args[:s].lower()
        name = args[s+1:]
        if platform == 'ps4':
            platform = 'psn'
        elif platform == 'xb1':
            platform = 'xbox'
        elif not platform in ['pc','xbox','psn']:
            platform = 'pc'
            name = args
    except ValueError:
        platform = 'pc'
        name = args
    if sql is not None:
        if len(name) < 1:
            data = sql.get_link(author)
            if data != None:
                name = data['user_nickname']
                platform = data['user_platform']
                linked = True
        else:
            try:
                user = parse_user_at(name,server)
                data = sql.get_link(user.id)
                if data != None:
                    name = data['user_nickname']
                    platform = data['user_platform']
                    linked = True
            except RuntimeError:
                pass
    return {'platform':platform, 'name':name, 'linked':linked}
