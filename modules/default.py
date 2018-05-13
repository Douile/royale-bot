from .module import Module, Command, checkPermissions, QueueAction, get_prefix, Map
import discord
import asyncio
import traceback

class DefaultModule(Module):
    def __init__(self,modules=[],version='',client_id=''):
        super().__init__(name='default',client_id=client_id)
        self.types = []
        self.modules = modules
        for module in modules:
            self.types = self.types + module.types
        self.modules.append(self)
        self.commands = {
            'status': Status(version),
            'help': Help(self.modules),
            'setchannel': SetChannel(self.types),
            'resetchannels': ResetChannels(self.types),
            'channels': Channels(self.types),
            'setprefix': SetPrefix()
        }
class Status(Command):
    def __init__(self,version):
        super().__init__(name='status',description="Print the status of the bot. `{prefix}status`")
        self.version = Map(version)
    def run(self,command,msg,settings):
        self.reset()
        raw = '<@!{author}> {name} {version_name} ({revison} {description}: {lines} lines) is online.'
        self.content = raw.format_map(self.version)
class Help(Command):
    def __init__(self,modules):
        super().__init__(name='help',description='Print out all the commands you can use. `{prefix}help`',aliases=['<@{bot_id}>','<@!{bot_id}>'])
        self.modules = modules
    def run(self,command,msg,settings):
        self.reset()
        self.is_help = True
        admin = msg.author.admin
        prefix = settings.get('prefix','!')
        if prefix == None:
            prefix = "!"
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
        self.embed.generate(self.modules)
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
        typemsg = self.typestring()
        super().__init__(name='setchannel',description='Set the channel to a command type. `{prefix}setchannel [arg]`.[arg] must be one of %s or `all`' % typemsg)
        self.permission = 'admin'
        self.types = types
    def run(self,command,msg,settings):
        self.reset()
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
            self.content = '<@!{0}> Successfully set {2} channel to <#{1}>'.format(msg.author.id,channelid,type)
        else:
            typemsg = self.typestring()
            self.content = '<@!{0}> You must specify the type to set this channel to one of: {1} or `all`'.format(msg.author.id,typemsg)
    def typestring(self):
        typemsg = ""
        for i in range(0,len(self.types)):
            typemsg += '`{0}`'.format(self.types[i])
            if i < len(self.types)-1:
                typemsg += ', '
        return typemsg
class ResetChannels(Command):
    def __init__(self,types=[]):
        super().__init__(name='resetchannels',description='Reset all set channels for this server. `{prefix}resetchannels`')
        self.permission = 'admin'
        self.types = types
    def run(self,command,msg,settings):
        self.reset()
        serverid = msg.server.id
        self.settings = {'channels':{}}
        for channeltype in self.types:
            self.settings['channels'][channeltype] = None
        self.content = '<@!{0}> Successfully reset all channels'.format(msg.author.id)
class Channels(Command):
    def __init__(self,types=[]):
        super().__init__(name='channels',description='Print set channels for current server. `{prefix}channels`')
        self.permission = 'admin'
        self.types = types
    def run(self,command,msg,settings):
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
        super().__init__(name='setprefix',description='Set the command prefix. `{prefix}setprefix "[prefix]"`.')
        self.permission = 'admin'
    def run(self,command,msg,settings):
        self.reset()
        if command.count('"') > 1:
            command = command[command.index('"')+1:]
            prefix = command[:command.index('"')]
        else:
            try:
                prefix = command.split(" ")[1]
            except IndexError:
                prefix = ''
        if prefix != '':
            self.content = '<@!{0}> Successfully set the prefix to {1}'.format(msg.author.id,prefix)
            self.settings = {'prefix':prefix}
        else:
            self.content = '<@!{0}> Please enter a valid prefix'.format(msg.author.id)

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
    def generate(self,modules):
        commands = {}
        for module in modules:
            if module.category == self.category:
                for command in module.commands:
                    cmd = module.commands[command]
                    if cmd.name != '':
                        if self.admin:
                            if cmd.description != '':
                                commands[command] = cmd.description
                            else:
                                commands[command] = 'Description not set'
                        else:
                            if cmd.permission != 'admin':
                                if cmd.description != '':
                                    commands[command] = cmd.description
                                else:
                                    commands[command] = 'Description not set'
                        if type(commands.get(command,None)) is str:
                            if len(cmd.aliases) > 0:
                                commands[command] += ' Aliases for this command are '
                                for alias in cmd.aliases:
                                    alias_format = alias.format_map(Map({'prefix':self.prefix}))
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
