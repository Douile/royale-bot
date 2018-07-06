from .module import Module, Command
from codemodules import modals
import asyncio

class TestingModule(Module):
    def __init__(self):
        super().__init__(name='testing',description='commands im testing',category='test')
        self.commands = {
            'acceptme': AcceptMe()
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
