import asyncio

class Module:
    def __init__(self,name="",description="",category=None):
        self.name = name
        self.description = description
        self.category = category
        self.commands = {}
        self.types = []
    @asyncio.coroutine
    def _run(self,empty,command,msg,settings):
        output = empty
        try:
            output = self.run(empty,command,msg,settings)
        except Exception as e:
            curcommand = msg.content[len(get_prefix(settings)):]
            for cmd in self.commands:
                if command.startswith(cmd) and isinstance(self.commands[cmd],Command):
                    if self.commands[cmd].permission != None:
                        if self.commands[cmd].permission != 'admin':
                            pcheck = checkPermissions(msg.channel.id,self.commands[cmd].permission,settings)
                        else:
                            pcheck = msg.author.server_permissions.administrator or msg.author.id == '293482190031945739'
                        if pcheck:
                            output = yield from self.commands[cmd]._run(curcommand,msg,settings)
                        else:
                            output.noPermission = self.commands[cmd].permission
                    else:
                        output = yield from self.commands[cmd]._run(curcommand,msg,settings)
        return output
class Command:
    def __init__(self,name="",description="",permission=None):
        self.name = name
        self.description = description
        self.permission = permission
        self.reset()
    @asyncio.coroutine
    def _run(self,command,msg,settings):
        self.reset()
        try:
            if callable(self.run):
                if asyncio.iscoroutinefunction(self.run):
                    yield from self.run()
                else:
                    self.run()
        except NameError:
            pass
        return self
    def reset(self):
        self.content = None
        self.file = None
        self.embed = None
        self.embeds = None
        self.settings = None
        self.shutdown = False
        self.noPermission = None
        self.typing = False
        self.deletes = []
        self.queue = []
    def changeSettings(self,settings):
        sets = settings
        if self.settings != None:
            sets = self.settings
        return sets
def checkPermissions(channel,type,settings):
    try:
        channel_id = settings['channels'].get(type)
        if channel_id == channel or channel_id == None:
            p = True
        else:
            p = False
    except KeyError:
        p = False
    return p
class QueueAction:
    def __init__(self,function,args=[]):
        self.function = function
        self.args = args


def get_prefix(settings):
    prefix = settings.get('prefix','!')
    if prefix == None:
        prefix = '!'
    return prefix
