class Module:
    def __init__(self,name="",description="",category=None):
        self.name = name
        self.description = description
        self.category = category
        self.commands = {}
        self.types = []
    def _run(self,empty,command,msg,settings):
        output = empty
        try:
            output = self.run(empty,command,msg,settings)
        except Exception as e:
            curcommand = msg.content[len(settings.get('prefix','!')):]
            for cmd in self.commands:
                if command.startswith(cmd) and isinstance(self.commands[cmd],Command):
                    if self.commands[cmd].permission != None:
                        if self.commands[cmd].permission != 'admin':
                            pcheck = checkPermissions(msg.channel.id,self.commands[cmd].permission,settings)
                        else:
                            pcheck = msg.author.server_permissions.administrator or msg.author.id == '293482190031945739'
                        if pcheck:
                            self.commands[cmd].run(curcommand,msg,settings)
                            output = self.commands[cmd]
                        else:
                            output.noPermission = self.commands[cmd].permission
                    else:
                        self.commands[cmd].run(curcommand,msg,settings)
                        output = self.commands[cmd]
        return output
class Command:
    def __init__(self,name="",description="",permission=None):
        self.name = name
        self.description = description
        self.permission = permission
        self.reset()
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
