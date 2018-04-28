from .module import Module, Command, checkPermissions, QueueAction
import discord

class DefaultModule(Module):
    def __init__(self,modules=[],version=''):
        super().__init__(name='default')
        self.types = []
        self.modules = modules
        for module in modules:
            self.types = self.types + module.types
        self.modules.append(self)
        self.commands = {
            'status': Status(version),
            'help': Help(self.modules),
            'adminhelp': AdminHelp(self.modules),
            'setchannel': SetChannel(self.types),
            'resetchannels': ResetChannels(self.types),
            'channels': Channels(self.types)
        }
    def run(self,empty,command,msg,settings):
        output = empty
        if command.startswith('help'):
            if msg.author.server_permissions.administrator:
                self.commands['adminhelp'].run(msg,settings)
                output = self.commands['adminhelp']
            else:
                self.commands['help'].run(msg,settings)
                output = self.commands['help']
        else:
            for cmd in self.commands:
                if command.startswith(cmd) and isinstance(self.commands[cmd],Command) and cmd != 'help':
                    if self.commands[cmd].permission != None:
                        if self.commands[cmd].permission != 'admin':
                            pcheck = checkPermissions(msg.channel.id,self.commands[cmd].permission,settings)
                        else:
                            pcheck = msg.author.server_permissions.administrator
                        if pcheck:
                            self.commands[cmd].run(msg,settings)
                            output = self.commands[cmd]
                        else:
                            output.noPermission = self.commands[cmd].permission
                    else:
                        self.commands[cmd].run(msg,settings)
                        output = self.commands[cmd]
        return output
class Status(Command):
    def __init__(self,version):
        super().__init__(name='status',description="Get the status of the bot")
        self.version = version
    def run(self,msg,settings):
        self.reset()
        raw = '<@!{0}> bot v{1} is online!'
        self.content = raw.format(msg.author.id,self.version)
class Help(Command):
    def __init__(self,modules):
        super().__init__(name='help',description='Print out all the commands you can use')
        self.modules = modules
    def run(self,msg,settings):
        self.reset()
        prefix = settings.get('prefix','!')
        commands = {}
        for module in self.modules:
            for command in module.commands:
                cmd = module.commands[command]
                if cmd.name != '' and cmd.permission != 'admin':
                    if cmd.description != '':
                        commands[command] = cmd.description
                    else:
                        commands[command] = 'Description not set'
        self.embed = discord.Embed(title="Help",type="rich",color=0x2ede2e)
        self.embed.set_thumbnail(url=msg.server.icon_url)
        for command in commands:
            description = commands[command]
            cmd = "{0}{1}".format(prefix,command)
            self.embed.add_field(name=cmd,value=description,inline=False)
class AdminHelp(Command):
    def __init__(self,modules):
        super().__init__()
        self.modules = modules
    def run(self,msg,settings):
        self.reset()
        prefix = settings.get('prefix','!')
        commands = {}
        for module in self.modules:
            for command in module.commands:
                cmd = module.commands[command]
                if cmd.name != '':
                    if cmd.description != '':
                        commands[command] = cmd.description
                    else:
                        commands[command] = 'Description not set'
        self.embed = discord.Embed(title="Help",type="rich",color=0x2ede2e)
        self.embed.set_thumbnail(url=msg.server.icon_url)
        for command in commands:
            description = commands[command]
            cmd = "{0}{1}".format(prefix,command)
            self.embed.add_field(name=cmd,value=description,inline=False)
class SetChannel(Command):
    def __init__(self,types=[]):
        self.types = types
        typemsg = self.typestring()
        super().__init__(name='setchannel',description='Set the channel to a command type. `!setchannel {arg}`.{arg} must be one of %s or `all`' % typemsg)
        self.permission = 'admin'
        self.types = types
    def run(self,msg,settings):
        self.reset()
        channelid = msg.channel.id
        try:
            type = msg.content.split(" ")[1].lower()
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
        super().__init__(name='resetchannels',description='Reset all set channels for this server. `!resetchannels`')
        self.permission = 'admin'
        self.types = types
    def run(self,msg,settings):
        self.reset()
        serverid = msg.server.id
        self.settings = {'channels':{}}
        for channeltype in self.types:
            self.settings['channels'][channeltype] = None
        self.content = '<@!{0}> Successfully reset all channels'.format(msg.author.id)
class Channels(Command):
    def __init__(self,types=[]):
        super().__init__(name='channels',description='Print set channels for current server. `!channels`')
        self.permission = 'admin'
        self.types = types
    def run(self,msg,settings):
        self.reset()
        serverid = msg.server.id
        name = '{0}\'s channels'.format(server['name'])
        self.embed = discord.Embed(title=name)
        self.embed.set_thumbnail(url=msg.server.icon_url)
        for channeltype in self.types:
            if channeltype in settings['channels']:
                if settings['channels'][channeltype] == None:
                    value = 'Not set'
                else:
                    value = '<#{0}>'.format(settings['channels'][channeltype])
            else:
                value = 'Not set (error)'
            self.embed.add_field(name=channeltype,value=value,inline=False)
