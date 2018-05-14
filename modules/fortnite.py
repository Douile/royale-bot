from .module import Module, Command, parse_user_at
from dataretrieval import aiofnotes, meta
from imagegeneration import shop, stats
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
            'setbackground': SetBackgrounds(),
            'news': News(),
            'servers': Servers(),
            'patchnotes': PatchNotes(),
            'link': Link(sql),
            'unlink': UnLink(sql)
        }
        self.types = ['stats','shop','news','status','autoshop','autostatus','autonews']
class Shop(Command):
    def __init__(self,fnbr_key):
        super().__init__(name="shop",description='Print an image of today\'s fortnite shop. `{prefix}shop`')
        self.permission = 'shop'
        self.fnbr_key = fnbr_key
    @asyncio.coroutine
    def run(self,command,msg,settings):
        try:
            shopdata = shop.getShopData(self.fnbr_key)
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
class Stats(Command):
    def __init__(self,tn_key,sql):
        super().__init__(name='stats',description='Gets the fortnite stats of a player. `{prefix}stats [platform] [player]` if you do not set platform it will default to pc, if you are linked and do not enter a player name it will default to your linked account, you can also @metion another linked user to default to their linked account.',permission='stats',aliases=['{prefix}'])
        self.tn_key = tn_key
        self.sql = sql
    @asyncio.coroutine
    def run(self,command,msg,settings):
        if command.startswith('stats'):
            args = command[len('stats'):].strip()
        else:
            args = command.strip()
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
        if len(name) < 1:
            data = self.sql.get_link(msg.author.id)
            if data != None:
                name = data['user_nickname']
        else:
            try:
                user = parse_user_at(name,msg.server.id)
                data = self.sql.get_link(user.id)
                if data != None:
                    name = data['user_nickname']
            except RuntimeError:
                pass
        try:
            logger.debug('Stats command name: %s platform %s', name, platform)
            bgs = settings.get('backgrounds',{})
            bgs_s = bgs.get('stat',[])
            statsimage = yield from stats.generate(self.tn_key,name,platform,bgs_s)
            if statsimage == None:
                self.content = '<@!{author}> User not found'
            else:
                self.typing = True
                statsimage.save('generatedstats.png')
                self.file = 'generatedstats.png'
        except Exception as e:
            self.content = "Error getting stats"
            logger.error(traceback.format_exc())
class Link(Command):
    def __init__(self,sql):
        super().__init__(name='link',description='Link you fortnite account for easy stats retrieval. `{prefix}link [username]`',permission='stats')
        self.sql = sql
    @asyncio.coroutine
    def run(self,command,msg,settings):
        command_size = len('link ')
        if len(command) > command_size:
            name = command[command_size:].strip()
            if len(name.strip()) > 0:
                self.content = '<@!{author}> Your account is now linked to `' + name + '`'
                try:
                    self.sql.set_link(msg.author.id,name)
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
        super().__init__(name='servers',description='Print the fortnite servers status. `{prefix}servers`')
        self.permission = 'status'
    def run(self,command,msg,settings):
        self.reset()
        status = meta.getStatus()
        self.content = '<@!{0}>'.format(msg.author.id)
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
        logger.debug('Fetched patch notes',extra=notes)
        if notes['success']:
            self.embed = PatchNotesEmbed(notes['notes'][0])
            if notes['notes'][0]['simple'] != None:
                self.content = notes['notes'][0]['simple']['video']
        else:
            self.content = 'Sorry <@!{author}> we were unable to get the patch notes'

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
        elif value == 'Degraded Performance' or value == 'Under Maintenance':
            level = 1
        elif value == 'Major Outage':
            level = 2
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
