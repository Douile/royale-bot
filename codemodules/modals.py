import asyncio
from discord import Embed

ACTION_TIMEOUT = 0.15

send_message = None
edit_message = None
delete_message = None
add_reaction = None
clear_reactions = None

active_modals = {}

def setup(send_function,edit_function,delete_function,reaction_function,clear_function):
    global send_message
    global edit_message
    global delete_message
    global add_reaction
    global clear_reactions
    send_message = send_function
    edit_message = edit_function
    delete_message = delete_function
    add_reaction = reaction_function
    clear_reactions = clear_function

@asyncio.coroutine
def reaction_handler(reaction,user):
    if user != reaction.message.author:
        modal = active_modals.get(reaction.message.id)
        if modal is not None:
            if modal.only is None or modal.only == user:
                action = modal.actions.get(reaction.emoji)
                if action is not None and callable(action):
                    if asyncio.iscoroutinefunction(action):
                        yield from action(reaction,user,modal)
                    else:
                        action(reaction,user,modal)


class Modal:
    def __init__(self,*,content=None,embed=None,only=None):
        self.actions = ModalActionList()
        self.content = content
        self.embed = embed
        self.only = only
    @asyncio.coroutine
    def send(self,destination):
        self.message = yield from send_message(destination,content=self.content,embed=self.embed)
        active_modals[self.message.id] = self
        for action in self.actions:
            yield from asyncio.sleep(ACTION_TIMEOUT)
            yield from add_reaction(self.message,action.emoji)
        return self.message
    def add_action(self,key,action):
        self.actions.append(ModalAction(emoji=key,action=action))
    @asyncio.coroutine
    def delete(self):
        yield from delete_message(self.message)
        active_modals.pop(self.message.id,None)
    @asyncio.coroutine
    def reset(self):
        if self.content != self.message.content or self.embed != self.message.embeds[0]:
            self.message = yield from edit_message(self.message,new_content=self.content,embed=self.embed)
        yield from clear_reactions(self.message)
        has_actions = False
        for action in self.actions:
            has_actions = True
            yield from asyncio.sleep(ACTION_TIMEOUT)
            yield from add_reaction(self.message,action.emoji)
        if not has_actions:
            active_modals.pop(self.message.id,None)

class ModalAction:
    def __init__(self,*,emoji=None,action=None):
        self.emoji = emoji
        self.action = action

class ModalActionList(list):
    def get(self,key):
        value = None
        for action in self:
            if action.emoji == key:
                value = action.action
                break
        return value


class AcceptModal(Modal):
    def __init__(self,*,content=None,embed=None,only=None,accept=None,decline=None):
        super().__init__(content=content,embed=embed,only=only)
        self.add_action(u'\u274E',decline)
        self.add_action(u'\u2705',accept)

class PagedModal(Modal):
    def __init__(self,*,center_actions=[],only=None):
        self.only = only
        self.page = None
        self.pages = []
        self.center_actions = center_actions
    @property
    def actions(self):
        actual_actions = [ModalAction(emoji=u'\u2B05',action=self.page_left)] + self.center_actions + [ModalAction(emoji=u'\u27A1',action=self.page_right)]
        return ModalActionList(actual_actions)
    @property
    def content(self):
        c = None
        if self.page is not None:
            c = self.pages[self.page-1].content
        return c
    @property
    def embed(self):
        c = None
        if self.page is not None:
            c = self.pages[self.page-1].embed
        return c
    @staticmethod
    @asyncio.coroutine
    def page_left(reaction,user,modal):
        if modal.page < 2:
            modal.page = len(modal.pages)
        else:
            modal.page -= 1
        yield from modal.reset()
    @staticmethod
    @asyncio.coroutine
    def page_right(reaction,user,modal):
        if modal.page > len(modal.pages) - 2:
            modal.page = 1
        else:
            modal.page += 1
        yield from modal.reset()
    def add_page(self,content=None,embed=None):
        self.pages.append(self.Page(content=content,embed=embed))
        if self.page is None:
            self.page = 1
    class Page:
        def __init__(self,*,content=None,embed=None):
            self.content = content
            self.embed = embed

class ItemModal(Modal):
    def __init__(self,*,parent=None,only=None,title='_ _',description='_ _'):
        self.parent = parent
        self.only = only
        self.items = []
        self.content = None
        self.embed = Embed(title=title,description=description)
    @property
    def actions(self):
        actual_actions = [ModalAction(emoji=u'\u274C',action=self.close)]
        if self.parent is not None:
            actual_actions += [ModalAction(emoji=u'\u2B05',action=self.parent.reset)]
        self.embed.clear_fields()
        for i in range(len(self.items)):
            item = self.items[i]
            emoji = self.get_char(i)
            actual_actions.append(ModalAction(emoji=emoji,action=None))
            self.embed.add_field(name=emoji,value=item.name,inline=False)
        return ModalActionList(actual_actions)
    @staticmethod
    def get_char(i):
        if i > -1 and i < 26:
            return chr(55356)+chr(56806+i)
        else:
            raise ValueError('Char must be between 0 and 25')
    @staticmethod
    @asyncio.corouine
    def close(reaction, user, modal):
        yield from modal.delete()
    def add_item(self,name='_ _',description=None,action=None):
        self.items.append(self.Item(name=name,description=description,action=action))
    class Item:
        def __init__(self,*,name='_ _',description=None,action=None):
            self.name = name
            self.description = description
            self.action = action
