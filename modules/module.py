import asyncio
from discord import Object
import traceback
import logging
from utils import getEnv

DEFAULT_PREFIX = getEnv("DEFAULT_PREFIX","!")

class Module:
    def __init__(self,name="",description="",category=None,client_id=''):
        self.name = name
        self.description = description
        self.category = category
        self.commands = {}
        self.types = []
        self.client_id = client_id
    @asyncio.coroutine
    def _run(self,empty,command,msg,settings):
        output = empty
        run = getattr(self,'run',None)
        if callable(run):
            output = self.run(empty,command,msg,settings)
        else:
            curcommand = msg.content[len(get_prefix(settings)):]
            for cmd in self.commands:
                is_command = False
                if command.startswith(cmd):
                    is_command = True
                if is_command and isinstance(self.commands[cmd],Command):
                    output = yield from self._run_command(empty,cmd,curcommand,msg,settings)
        return output
    @asyncio.coroutine
    def _run_alias(self,empty,command,msg,settings):
        output = empty
        run = getattr(self,'run',None)
        if callable(run):
            output = self.run(empty,command,msg,settings)
        else:
            for cmd in self.commands:
                is_command = False
                curcommand = msg.content[len(get_prefix(settings)):]
                for alias in self.commands[cmd].aliases:
                    alias_cmd = alias.format_map(Map({'prefix':get_prefix(settings),'bot_id':self.client_id})).strip()
                    if msg.content.startswith(alias_cmd):
                        is_command = True
                        curcommand = msg.content[len(alias_cmd):]
                if is_command and isinstance(self.commands[cmd],Command):
                    output = yield from self._run_command(empty,cmd,curcommand,msg,settings)
        return output
    @asyncio.coroutine
    def _run_command(self,empty,cmd,command,msg,settings):
        output = empty
        if self.commands[cmd].permission != None:
            if self.commands[cmd].permission != 'admin':
                pcheck = checkPermissions(msg.channel.id,self.commands[cmd].permission,settings)
            else:
                pcheck = msg.author.server_permissions.administrator or msg.author.id == '293482190031945739'
            if pcheck:
                output = yield from self.commands[cmd]._run(command,msg,settings)
            else:
                output.noPermission = self.commands[cmd].permission
        else:
            output = yield from self.commands[cmd]._run(command,msg,settings)
        return output
class Command:
    def __init__(self,name="",description="",permission=None,aliases=[]):
        self.name = name
        self.description = description
        self.permission = permission
        self.aliases = aliases
        self.reset()
    @asyncio.coroutine
    def _run(self,command,msg,settings):
        self.reset()
        try:
            if callable(self.run):
                if asyncio.iscoroutinefunction(self.run):
                    yield from self.run(command,msg,settings)
                else:
                    self.run(command,msg,settings)
        except:
            error = traceback.format_exc()
            logging.getLogger('module').error('Error running command %s', error)
            self.noPermission = 'error'
        if self.content != None:
            self.content = self.content.format_map(Map({'author':msg.author.id,'channel':msg.channel.id,'server':msg.server.id,'prefix':settings['prefix']}))
        return self
    def reset(self):
        self.content = None
        self.file = None
        self.embed = None
        self.embeds = None
        self.custom = None
        self.settings = None
        self.is_help = False
        self.noPermission = None
        self.typing = False
        self.delete_command = False
        self.deletes = []
        self.queue = []
    def changeSettings(self,settings):
        sets = settings
        if self.settings != None:
            sets = self.settings
        return sets
    @property
    def empty(self):
        if self.content is None and \
             self.file is None and \
             self.embed is None and \
             self.embeds is None and \
             self.noPermission is None and \
             self.deletes == [] and \
             self.queue == [] and \
             self.custom is None:
            is_empty = True
        else:
            is_empty = False
        return is_empty
    def __iter__(self):
        yield 'content', self.content
        yield 'file', self.file
        yield 'embed', self.embed
        yield 'embeds', self.embeds
        yield 'settings', self.settings
        yield 'is_help', self.is_help
        yield 'noPermission', self.noPermission
        yield 'typing', self.typing
        yield 'delete_command', self.delete_command
        yield 'deletes', self.deletes
        yield 'queue', self.queue
    def debug(self, logger):
        logger.debug('message object: %s', str(dict(self)))


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
    prefix = settings.get('prefix',DEFAULT_PREFIX)
    if prefix == None:
        prefix = DEFAULT_PREFIX
    return prefix

def parse_user_at(text,serverid):
    if text.startswith('<@!'):
        id = text[3:-1]
    elif text.startswith('<@'):
        id = text[2:-1]
    elif text.startswith('<'):
        id = text[1:-1]
    else:
        raise RuntimeError('No user found')
    user = Object(id)
    user.server = Object(serverid)
    return user

class Map(dict):
    def __missing__(self, key):
        return "{"+key+"}"
