class Module:
    def __init__(self,name="",description=""):
        self.name = name
        self.description = description
        self.commands = {}
        self.types = []
    def _run(self,empty,command,msg,settings):
        output = empty
        try:
            output = self.run(empty,command,msg,settings)
        except Exception as e:
            for cmd in self.commands:
                if command.startswith(cmd) and isinstance(self.commands[cmd],Command):
                    if self.commands[cmd].permission != None:
                        if self.commands[cmd].permission != 'admin':
                            pcheck = checkPermissions(msg.channel.id,self.commands[cmd].permission,settings['servers'][msg.server.id])
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
        if settings['channels'][type] == channel or settings['channels'][type] == '' or not type in settings['channels']:
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
