import asyncio
from datetime import datetime, timezone

class Times:
    MINS_2 = list(range(0,60,2))
    MINS_5 = list(range(0,60,5))
    MINS_10 = list(range(0,60,10))
    HOURS_3 = list(range(0,24,3))
    HOURS_6 = list(range(0,24,6))

class Dispatcher:
    """Cron like event dispatcher"""
    class Event:
        def __init__(self,event,*,hours=None,minutes=None,pass_client=False):
            if not callable(event):
                raise ValueError('Event must be callable')
            self.event = event
            self.hours = hours
            self.minutes = minutes
            self.pass_client = pass_client
            self._task = None
        @asyncio.coroutine
        def dispatch(self,loop,client):
            if self.pass_client:
                args = [client]
            else:
                args = []
            if asyncio.iscoroutinefunction(self.event):
                self._task = loop.create_task(self.event(*args))
            else:
                self.event(*args)
        @staticmethod
        def check(checker,value):
            if checker is None:
                return True
            elif isinstance(checker,list):
                if value in checker:
                    return True
            elif isinstance(checker,int):
                if value == checker:
                    return True
            return False
        @asyncio.coroutine
        def call(self,time,loop,client):
            if isinstance(self._task,asyncio.Task):
                if not self._task.done():
                    return 1
            if self.check(self.hours,time.hour) and self.check(self.minutes,time.minute):
                yield from self.dispatch(loop,client)
            return 0

    def __init__(self):
        self._registered = []
        self._stop = False
    def register(self,*args,**kwargs):
        """
        Register a new event on this dispatcher
        See Dispatcher.Event for params
        """
        event = self.Event(*args,**kwargs)
        self._registered.append(event)
    @asyncio.coroutine
    def run(self,client=None):
        """Main event loop for dispatcher"""
        loop = getattr(client,'loop',None)
        if loop is None:
            loop = asyncio.get_event_loop()
        while self._stop == False:
            print('Did update')
            time = datetime.now(tz=timezone.utc)
            for event in self._registered:
                loop.create_task(event.call(time,loop,client))
            yield from asyncio.sleep(60)
