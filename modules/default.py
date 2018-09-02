from .module import Module, Command, checkPermissions, QueueAction, get_prefix, Map
from codemodules import modals
import discord
import asyncio
import traceback
import logging
from utils import getEnv, arrays
import localisation

DEFAULT_PREFIX = getEnv("DEFAULT_PREFIX","!")
UPDATE_SERVER = None


class DefaultModule(Module):
    def __init__(self,modules=[],version='',client_id='',database=None):
        super().__init__(name='default',client_id=client_id)
        global UPDATE_SERVER
        if database is not None:
            UPDATE_SERVER = database.set_server_info
        self.types = []
        self.modules = modules
        for module in modules:
            self.types = self.types + module.types
        self.modules.append(self)
        self.commands = {
            'botinfo': Status(version),
            'help': Help(self.modules),
            'setchannel': SetChannel(self.types),
            'resetchannels': ResetChannels(self.types),
            'channels': Channels(self.types),
            'setprefix': SetPrefix(),
            'setlocale': SetLocale()
        }
class Status(Command):
    def __init__(self,version):
        super().__init__(name='botinfo',description=localisation.PreMessage('botinfo_help'))
        self.version = Map(version)
    @asyncio.coroutine
    def run(self,client,command,msg,settings):
        raw = '<@!{author}> {name} {version_name} ({revison} {description}: {lines} lines) is online.) shards: {shards}'
        self.content = raw.format_map(self.version)
class Help(Command):
    def __init__(self,modules):
        super().__init__(name='help',description='Print out all the commands you can use. `{prefix}help`',aliases=['<@{bot_id}>','<@!{bot_id}>'])
        self.modules = modules
    def run(self,client,command,msg,settings):
        self.reset()
        self.is_help = True
        admin = msg.author.server_permissions.administrator
        prefix = settings.get('prefix',DEFAULT_PREFIX)
        if prefix == None:
            prefix = DEFAULT_PREFIX
        try:
            cmd = command.split(" ")[0].lower()
            if cmd.count('-u') > 0:
                admin = False
            if cmd.count('-d') > 0:
                self.is_help = False
        except:
            pass
        try:
            category = command.split(" ")[1].lower()
        except IndexError:
            category = None
        self.embed = HelpEmbed(prefix=prefix,category=category,icon_url=msg.server.icon_url,admin=admin)
        self.embed.generate(self.modules,lang=settings.get('locale'))
        last_help_msg = settings.get('last_help_msg',None)
        if last_help_msg != None:
            last_help = discord.Object(last_help_msg)
            last_help.channel = discord.Object(settings.get('last_help_channel'))
            self.queue = [QueueAction(remove_help,[last_help])]
@asyncio.coroutine
def remove_help(client,msg):
    try:
        yield from client.delete_message(msg)
    except:
        traceback.print_exc()
class SetChannel(Command):
    def __init__(self,types=[]):
        self.types = types
        super().__init__(name='setchannel',description=localisation.PreMessage('setchannel_help',types=arrays.message_string(self.types,'all')))
        self.permission = 'admin'
        self.types = types
    @asyncio.coroutine
    def run(self,client,command,msg,settings):
        locale = settings.get('locale')
        channelid = msg.channel.id
        try:
            type = command.split(" ")[1].lower()
        except IndexError:
            type = ""
        success = False
        self.settings = {'channels':{}}
        if type == 'all':
            for channeltype in self.types:
                self.settings['channels'][channeltype] = channelid
            success = True
        else:
            for channeltype in self.types:
                if type == channeltype:
                    self.settings['channels'][channeltype] = channelid
                    success = True
        if success:
            self.content = localisation.getFormattedMessage('setchannel_success',author=msg.author.id,channel=channelid,type=type,lang=locale)
        else:
            typemsg = arrays.message_string(self.types,'all')
            self.content = localisation.getFormattedMessage('setchannel_error',author=msg.author.id,types=typemsg,lang=locale)
class ResetChannels(Command):
    def __init__(self,types=[]):
        self.types = types
        super().__init__(name='resetchannels',description=localisation.PreMessage('resetchannels_help',types=arrays.message_string(self.types,'all')))
        self.permission = 'admin'
    @asyncio.coroutine
    def run(self,client,command,msg,settings):
        locale = settings.get('locale')
        serverid = msg.server.id
        try:
            type = command.split(" ")[1].lower()
        except IndexError:
            type = None
        if type is None:
            self.settings = {'channels':{}}
            for channeltype in self.types:
                self.settings['channels'][channeltype] = None
            self.content = localisation.getFormattedMessage('resetchannels_all',author=msg.author.id,lang=locale)
        else:
            if type in self.types:
                self.settings['channels'] = {}
                self.settings['channels'][type] = None
                self.content = localisation.getFormattedMessage('resetchannels_success',author=msg.author.id,type=type,lang=locale)
            else:
                self.content = localisation.getFormattedMessage('resetchannels_error',author=msg.author.id,lang=locale)
class Channels(Command):
    def __init__(self,types=[]):
        super().__init__(name='channels',description=localisation.PreMessage('channels_help'))
        self.permission = 'admin'
        self.types = types
    def run(self,client,command,msg,settings):
        self.reset()
        serverid = msg.server.id
        name = '{0}\'s channels'.format(settings.get('server_name',''))
        self.embed = discord.Embed(title=name)
        self.embed.set_thumbnail(url=msg.server.icon_url)
        for channeltype in self.types:
            if channeltype in settings['channels']:
                if settings['channels'][channeltype] == None:
                    value = 'Not set'
                else:
                    value = '<#{0}>'.format(settings['channels'][channeltype])
            else:
                value = 'Not set'
            self.embed.add_field(name=channeltype,value=value,inline=False)
class SetPrefix(Command):
    def __init__(self):
        super().__init__(name='setprefix',description=localisation.PreMessage('setprefix_help'))
        self.permission = 'admin'
    @asyncio.coroutine
    def run(self,client,command,msg,settings):
        locale = settings.get('locale')
        if command.count('"') > 1:
            command = command[command.index('"')+1:]
            prefix = command[:command.index('"')]
        else:
            try:
                prefix = command.split(" ")[1]
            except IndexError:
                prefix = ''
        if prefix != '':
            text = localisation.getFormattedMessage('setprefix_confirm',author=msg.author.id,prefix=prefix,lang=locale)
            self.custom = modals.AcceptModal(client,content=text,accept=self.acceptModal,decline=self.declineModal,only=msg.author)
            self.custom.prefix = prefix
            self.custom.locale = locale
            yield from self.custom.send(msg.channel)
            # self.content = '<@!{0}> Successfully set the prefix to `{1}`'.format(msg.author.id,prefix)
            # self.settings = {'prefix':prefix}
        else:
            self.content = localisation.getFormattedMessage('setprefix_invalid',author=msg.author.id,lang=locale)
    @staticmethod
    @asyncio.coroutine
    def acceptModal(reaction,user,modal):
        modal.content = localisation.getFormattedMessage('setprefix_changing',prefix=modal.prefix,lang=modal.locale)
        modal.actions = {}
        yield from modal.reset()
        yield from update_prefix(modal.message.server.id,modal.prefix,
            finish_modal(modal,localisation.getFormattedMessage('setprefix_success',prefix=modal.prefix,lang=modal.locale)),
            finish_modal(modal,localisation.getMessage('setprefix_error',lang=modal.locale))
        )
    @staticmethod
    @asyncio.coroutine
    def declineModal(reaction,user,modal):
        modal.content = localisation.getMessage('setprefix_decline')
        modal.actions = {}
        yield from modal.reset()
@asyncio.coroutine
def update_prefix(server,prefix,done,error):
    global UPDATE_SERVER
    if UPDATE_SERVER is None:
        yield from error
    else:
        try:
            UPDATE_SERVER(server,prefix=prefix)
            yield from done
        except:
            error_text = traceback.format_exc()
            logging.getLogger('update_prefix').error('Error updating prefix: %s',error_text)
            yield from error
class SetLocale(Command):
    def __init__(self):
        super().__init__(name='setlocale',description=localisation.PreMessage('setlocale_help'),permission='admin')
    @asyncio.coroutine
    def run(self,client,command,msg,settings):
        locale = settings.get('locale')
        embed = LocaleEmbed(locale=locale)
        self.custom = modals.Modal(client,embed=embed,only=msg.author)
        self.custom.locale = locale
        self.custom.add_action(u'\u274C',self.cancel)
        self.custom.flagMap = embed.flags
        for flag in self.custom.flagMap:
            self.custom.add_action(flag,self.change_language)
        yield from self.custom.send(msg.channel)
    @staticmethod
    @asyncio.coroutine
    def cancel(reaction,user,modal):
        modal.embed = TextEmbed(text=localisation.getMessage('setlocale_cancel',lang=modal.locale))
        modal.actions = {}
        yield from modal.reset()
    @staticmethod
    @asyncio.coroutine
    def change_language(reaction,user,modal):
        locale = modal.flagMap.get(str(reaction.emoji))
        modal.embed = TextEmbed(text=localisation.getFormattedMessage('setlocale_change',locale=locale,lang=modal.locale))
        modal.actions = {}
        yield from modal.reset()
        yield from update_locale(modal.message.server.id,locale,
            finish_modal(modal,embed=localisation.getFormattedMessage('setlocale_success',locale=locale,lang=locale)),
            finish_modal(modal,embed=localisation.getMessage('setlocale_error',lang=modal.locale))
        )
class LocaleEmbed(discord.Embed):
    def __init__(self,locale=None):
        super().__init__(title=localisation.getMessage('setlocale_title',lang=locale),description=localisation.getMessage('setlocale_desc',lang=locale),color=0x6ad2f7)
        self.flags = {}
        locales = localisation.getLocales()
        for localeInfo in locales:
            if localeInfo.lang == 'en':
                country = 'GB'
            elif localeInfo.lang == 'pt-br':
                country = 'BR'
            else:
                country = localeInfo.lang
            flag = self.getFlag(country)
            self.flags[flag] = localeInfo.lang
            title = '{} {}'.format(flag,localeInfo.name)
            if localeInfo.name != localeInfo.nameEn:
                title += ' (' + localeInfo.nameEn + ')'
            value = localisation.getFormattedMessage('setlocale_value',lang=locale,author=localeInfo.author)
            self.add_field(name=title,value=value,inline=False)
    @staticmethod
    def getFlag(country):
        country = country.upper()
        flag = ''
        for char in country:
            flag += chr(ord(char)+127397)
        return flag
@asyncio.coroutine
def update_locale(server,locale,done,error):
    global UPDATE_SERVER
    logger = logging.getLogger('update_locale')
    if UPDATE_SERVER is None:
        yield from error
        error_text = traceback.format_exc()
        logger.error('Error updating locale: %s',error_text)
    else:
        try:
            UPDATE_SERVER(server,locale=locale)
            yield from done
            logger.debug('Updated locale to %s for %s',locale,server)
        except:
            error_text = traceback.format_exc()
            logger.error('Error updating locale: %s',error_text)
            yield from error
@asyncio.coroutine
def finish_modal(modal,content=None,embed=None):
    modal.content = content
    if embed is not None:
        modal.embed = TextEmbed(text=embed)
    else:
        modal.embed = None
    modal.actions = {}
    yield from modal.reset()
class TextEmbed(discord.Embed):
    def __init__(self,text='_ _',description=None,footer=None):
        super().__init__(title=text,description=description,color=0x6ad2f7)
        if footer is not None:
            self.set_footer(text=footer)

class HelpEmbed(discord.Embed):
    def __init__(self,prefix='!',category=None,icon_url=None,admin=False):
        super().__init__(title="Help",color=0x2ede2e)
        self.prefix = prefix
        self.category = category
        self.admin = admin
        if icon_url != None:
            self.set_thumbnail(url=icon_url)
        if self.category != None:
            self.title = "Help ({0})".format(self.category)
    def generate(self,modules,lang=None):
        commands = {}
        for module in modules:
            if module.category == self.category:
                for command in module.commands:
                    cmd = module.commands[command]
                    if cmd.name != '':
                        if self.admin:
                            if cmd.description != '':
                                if localisation.is_pre(cmd.description):
                                    commands[command] = cmd.description.getMessage(lang=lang)
                                else:
                                    commands[command] = str(cmd.description)
                            else:
                                commands[command] = 'Description not set'
                        else:
                            if cmd.permission != 'admin':
                                if cmd.description != '':
                                    if localisation.is_pre(cmd.description):
                                        commands[command] = cmd.description.getMessage(lang=lang)
                                    else:
                                        commands[command] = str(cmd.description)
                                else:
                                    commands[command] = 'Description not set'
                        if type(commands.get(command,None)) is str:
                            if len(cmd.aliases) > 0:
                                commands[command] += ' Aliases for this command are '
                                for alias in cmd.aliases:
                                    alias_format = alias.format_map(Map({'prefix':self.prefix,'bot_id':'424265028267540490'})) # change from hard coding
                                    if alias_format.startswith('<@'):
                                        commands[command] += '{}, '.format(alias_format)
                                    else:
                                        commands[command] += '`{}`, '.format(alias_format)
                                if commands[command].endswith(', '):
                                    commands[command] = commands[command][:-2]
        if self.admin and commands.get('help',None) != None:
            commands['help'] += ' Add `-u` to print non admin help as admin, add `-d` to never auto delete the help message. E.g. `{prefix}help-u-d` will print a help message for normal users that never gets deleted.'
        is_commands = False
        for command in commands:
            description = commands[command].format_map(Map({'prefix':self.prefix}))
            cmd = "{0}{1}".format(self.prefix,command)
            self.add_field(name=cmd,value=description,inline=False)
            is_commands = True
        if self.category == None:
            categories = {}
            for module in modules:
                if module.category != None:
                    categories[module.category] = module.description
            for category in categories:
                title = "{0}help {1}".format(self.prefix,category)
                description = categories[category].format_map({'prefix':self.prefix})
                self.add_field(name=title,value=description,inline=False)
        if self.category != None and is_commands == False:
            description = "You can find categories using {0}help".format(self.prefix)
            self.add_field(name="No commands in this category",value=description,inline=False)
