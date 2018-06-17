from .module import Module, Command, parse_user_at
from dataretrieval import aiofnotes, meta
from imagegeneration import shop, stats
from utils import strings
import traceback
from datetime import datetime
import discord
import asyncio
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
            'servers': Servers(),
            'patchnotes': PatchNotes(),
            'link': Link(sql),
            'unlink': UnLink(sql)
        }
        self.types = ['autoshop','autostatus','autonews']
        for command_name in self.commands:
            command = self.commands[command_name]
            if command.permission is not None and not command.permission in self.types and command.permission != 'admin':
                self.types.append(command.permission)
class Shop(Command):
    def __init__(self,fnbr_key):
        super().__init__(name="shop",description='Print an image of today\'s fortnite shop. `{prefix}shop`')
        self.permission = 'shop'
        self.fnbr_key = fnbr_key
    @asyncio.coroutine
    def run(self,command,msg,settings):
        logger = logging.getLogger('shop-command')
        try:
            shopdata = yield from shop.getShopData(self.fnbr_key)
            if shopdata.status == 200:
                bgs = settings.get('backgrounds',{})
                bgs_s = bgs.get('shop',[])
                logger.debug('Generating shop')
                file = yield from shop.generate(shopdata,bgs_s,msg.server.id)
                self.typing = True
                self.file = file
                self.content = "Data from <https://fnbr.co>"
                self.settings = {'latest_shop': file}
            else:
                self.content = "Sorry there was an api error: {0}. All data from <https://fnbr.co>".format(shopdata.status)
                if 'latest_shop' in settings and settings['latest_shop'] != '':
                    self.file = settings['latest_shop']
        except Exception as e:
            self.content = "Error generating image"
            logger.error(traceback.format_exc())
class Upcoming(Command):
    def __init__(self,fnbr_key):
        super().__init__(name="upcoming",description='Print currently found upcoming fortnite items. `{prefix}upcoming`')
        self.permission = 'shop'
        self.fnbr_key = fnbr_key
    @asyncio.coroutine
    def run(self,command,msg,settings):
        logger = logging.getLogger('upcomming-command')
        try:
            data = yield from upcoming.getData(self.fnbr_key)
            if data.status == 200:
                bgs = settings.get('backgrounds',{})
                bgs_s = bgs.get('shop',[])
                logger.debug('Generating shop')
                file = yield from upcoming.generate(data,bgs_s,msg.server.id)
                self.typing = True
                self.file = file
                self.content = "Data from <https://fnbr.co>"
            else:
                self.content = "Sorry there was an api error: {0}. All data from <https://fnbr.co>".format(shopdata.status)
        except Exception as e:
            self.content = "Error generating image"
            logger.error(traceback.format_exc())

class Stats(Command):
    def __init__(self,tn_key,sql):
        super().__init__(name='stats',description='Gets the fortnite stats of a player. `{prefix}stats [platform] [player]` if you do not set platform it will default to pc, if you are linked and do not enter a player name it will default to your linked account, you can also @metion another linked user to default to their linked account.',permission='stats',aliases=['{prefix}'])
        self.tn_key = tn_key
        self.sql = sql
    @asyncio.coroutine
    def run(self,command,msg,settings):
        logger = logging.getLogger('matches')
        if command.startswith('stats'):
            args = command[len('stats'):].strip()
        else:
            args = command.strip()
        type = 'regular'
        match = strings.startmatches(args, ['s4','season4','cs','currentseason'])
        if match is not None:
            args = args[len(match):]
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
                statsimage = yield from stats.generate(self.tn_key,name,platform,bgs_s)
                if statsimage == None:
                    if linked:
                        self.content = 'User not found using your linked account: `{0}` (`{1}`). You might need to update your linked account using `{2}link [username]`'.format(name,platform,'{prefix}')
                    else:
                        self.content = 'User not found: `{0}` (`{1}`)'.format(name,platform)
                else:
                    self.typing = True
                    statsimage.save('generatedstats.png')
                    self.content = '<https://fortnitetracker.com/profile/{1}/{0}>'.format(name,platform)
                    self.file = 'generatedstats.png'
            except Exception as e:
                if linked:
                    self.content = "Error getting stats with your linked account: `{0}` (`{1}`). You might need to update your linked account using the `{2}link [username]` command.".format(name,platform,'{prefix}')
                else:
                    self.content = "Error getting stats for `{0}` (`{1}`)".format(name,platform)
                logger.error(traceback.format_exc())
        else:
            if linked:
                self.content = 'Your linked account name `{0}` (`{1}`) is too short please relink using `{2}link [username]`'.format(name,platform,'{prefix}')
            else:
                self.content = '<@!{author}> you must link your account using `{prefix}link [username]`, or just enter your name in this command.'
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
        super().__init__(name='link',description='Link you fortnite account for easy stats retrieval. `{prefix}link [platform]? [username]` if you do not include platform or if it is not one of `pc`, `xbox` or `psn` it will default to `pc`',permission='stats')
        self.sql = sql
    @asyncio.coroutine
    def run(self,command,msg,settings):
        command_size = len('link ')
        if len(command) > command_size:
            user = yield from parse_fortnite_user(command[command_size:])
            name = user.get('name')
            platform = user.get('platform')
            if len(name.strip()) > 0:
                self.content = '<@!{2}> Your account is now linked to `{0}` (`{1}`)'.format(name,platform,'{author}')
                try:
                    self.sql.set_link(msg.author.id,name,platform)
                except:
                    traceback.print_exc()
                    self.content = '<@!{author}> Sorry we had an error linking your account'
            else:
                self.content = '<@!{author}> Please provide a username to link to'
        else:
            self.content = '<@!{author}> You must enter a username to link your account'
class UnLink(Command):
    def __init__(self,sql):
        super().__init__(name='unlink',description='Unlink your fortnite account. `{prefix}unlink`',permission='stats')
        self.sql = sql
    @asyncio.coroutine
    def run(self,command,msg,settings):
        try:
            self.sql.delete_link(msg.author.id)
            self.content = '<@!{author}> Account successfully unlinked'
        except:
            traceback.print_exc()
            self.content = '<@!{author}> Sorry there was an error unlinking your account'
class SetBackgrounds(Command):
    def __init__(self):
        self.background_types = ['shop','stat']
        super().__init__(name='setbackground',description='Sets the backgrounds for all images generated. Seperate urls with a space. If you want a blank backround don\'t include any urls. `{prefix}setbackground(s) [type] [url 2] [url 3]...`. `type` must be one of '+str(self.background_types))
        self.permission = 'admin'
    def run(self,command,msg,settings):
        self.reset()
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
        self.settings = {'backgrounds': {type:backgrounds}}
        self.content = '<@!{author}> Set backgrounds'
class News(Command):
    def __init__(self):
        super().__init__(name='news',description='Print the current news in fortnite battle royale. `{prefix}news`')
        self.permission = 'news'
    def run(self,command,msg,settings):
        self.reset()
        news = meta.getNews('en')
        if news['success']:
            self.embeds = []
            for msg in news['messages']:
                embed = NewsEmbed(msg,news['updated'])
                self.embeds.append(embed)
        else:
            self.content = 'Sorry <@!{author}> we were unable to get the news.'
class Servers(Command):
    def __init__(self):
        super().__init__(name='servers',description='Print the fortnite servers status. `{prefix}servers`',permission='servers')
    @asyncio.coroutine
    def run(self,command,msg,settings):
        status = yield from meta.getStatus()
        self.content = '<@!{0}> current server status'.format(msg.author.id)
        self.embed = StatusEmbed(status['online'],status['message'])
        for s in status['services']:
            self.embed.add_service(name=s,value=status['services'][s])
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
