from .module import Module, Command
from .data import shop,statsimages,meta
import traceback
import time
from datetime import datetime
import os.path
import discord
import asyncio

class FortniteModule(Module):
    def __init__(self,fnbr_key='',tn_key=''):
        super().__init__(name="Fortnite",description="Commands related to fortnite",category="fortnite")
        self.commands = {
            'shop': Shop(fnbr_key),
            'stats': Stats(tn_key),
            'setbackground': SetBackgrounds(),
            'news': News(),
            'servers': Servers(),
            'patchnotes': PatchNotes()
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
                rawtime = shop.getTime(shopdata.data.date)
                rtime = time.mktime(rawtime.utctimetuple())
                now = time.mktime(datetime.utcnow().utctimetuple())
                tommorow = rtime + (60*60*24)
                if now > tommorow or not os.path.isfile(shop.filename(rawtime)):
                    if 'backgrounds' in settings:
                        backgrounds = settings['backgrounds']
                    else:
                        backgrounds = []
                    print('Generating shop')
                    file = yield from shop.generate(shopdata,backgrounds,msg.server.id)
                else:
                    file = shop.filename(rawtime)
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
            print(e)
            traceback.print_exc()
class Stats(Command):
    def __init__(self,tn_key):
        super().__init__(name='stats',description='Gets the fortnite stats of a player. `{prefix}stats [platform] [player]` if you do not set platform it will default to pc')
        self.permission = 'stats'
        self.tn_key = tn_key
    @asyncio.coroutine
    def run(self,command,msg,settings):
        args = command[len('stats'):].strip()
        try:
            s = args.index(' ')
            platform = args[:s]
            name = args[s+1:]
            if platform == 'ps4':
                platform = 'psn'
            elif not platform in ['pc','xb1','psn']:
                platform = 'pc'
        except ValueError:
            platform = 'pc'
            name = args
        try:
            print('Name: '+name)
            print('Platform: '+platform)
            statsimage = yield from statsimages.generate(self.tn_key,name,platform,settings.get('backgrounds',[]))
            if statsimages == None:
                self.content = '<@!{author}> User not found'
            else:
                self.typing = True
                statsimage.save('generatedstats.png')
                self.content = '<@!{author}>'
                self.file = 'generatedstats.png'
        except Exception as e:
            self.content = "Error getting stats"
            print(e)
            traceback.print_exc()
class SetBackgrounds(Command):
    def __init__(self):
        super().__init__(name='setbackground',description='Sets the backgrounds for all images generated. Seperate urls with a space. If you want a blank backround don\'t include any urls. `{prefix}setbackground(s) [url 1] [url 2] [url 3]...`')
        self.permission = 'admin'
    def run(self,command,msg,settings):
        self.reset()
        urls = command.split(" ")
        if len(urls) < 2:
            backgrounds = []
        else:
            backgrounds = urls[1:]
        self.settings = {'backgrounds': backgrounds}
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
        super().__init__(name='patchnotes',description="Get the latest patchnotes. `{prefix}patchnotes ([d], [detail])` include `d` or `detail` for a more detailed breakdown of the patchnotes.")
        self.permission = 'news'
    def run(self,command,msg,settings):
        self.reset()
        args = msg.content.split(" ")
        try:
            arg = args[1].lower()
        except IndexError:
            arg = ''
        if arg == 'd' or arg == 'detail':
            detailed = True
        else:
            detailed = False
        notes = meta.getPatchNotes(1,0,detailed)
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
            if note['simple']['video'] != None:
                self.set_video(url=note['simple']['video'])
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
