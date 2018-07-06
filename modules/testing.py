from .module import Module, Command
from discord import Embed
from codemodules import modals
from random import randint
import asyncio

class TestingModule(Module):
    def __init__(self):
        super().__init__(name='testing',description='commands im testing',category='testing')
        self.commands = {
            'acceptme': AcceptMe(),
            'testpages': TestPages()
        }

class AcceptMe(Command):
    def __init__(self):
        super().__init__(name='acceptme',description='A test accept modal',permission='admin')
    @asyncio.coroutine
    def run(self,command,msg,settings):
        self.custom = modals.AcceptModal(content='Would you like to accept?',accept=self.accept,decline=self.decline)
        yield from self.custom.send(msg.channel)
    @staticmethod
    @asyncio.coroutine
    def accept(reaction, user, modal):
        modal.content = 'You accepted'
        modal.actions = {}
        yield from modal.reset()
    @staticmethod
    @asyncio.coroutine
    def decline(reaction, user, modal):
        modal.content = 'You declined'
        modal.actions = {}
        yield from modal.reset()

class TestPages(Command):
    def __init__(self):
        super().__init__(name='testpages',description='A test paged modal',permission='admin')
    @asyncio.coroutine
    def run(self,command,msg,settings):
        self.custom = modals.PagedModal(center_actions=[modals.ModalAction(emoji=u'\u274C',action=self.end)])
        size = randint(3,15)
        for i in range(1,size+1):
            self.custom.add_page(embed=self.Page(i,size))
        yield from self.custom.send(msg.channel)
    @staticmethod
    @asyncio.coroutine
    def end(reaction,user,modal):
        yield from modal.delete()
    class Page(Embed):
        def __init__(self,number,amount):
            super().__init__(title='Page {}'.format(number),description='You can close this by pressing the :x:')
            self.set_footer(text='{}/{}'.format(number,amount))
