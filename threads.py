import threading, queue, asyncio
from imagegeneration import shop, stats, upcoming
import bot

class Queue(queue.Queue):
    def find(self, test):
        """ Provide a test function to check all items in queue """
        i = 0
        for item in self.queue:
            if test(item):
                i += 1
        return i

class WorkerThread(threading.Thread):
    def __init__(self):
        super(WorkerThread, self).__init__()
        self.input = Queue()
        self.output = Queue()
        self. = Queue()
        self.stoprequest = threading.Event()

class ShopImage(WorkerThread):
    class Request:
        def __init__(self,requestId,*,apikey=None,serverid=None,backgrounds=[]):
            self.apikey = apikey
            self.serverid = serverid
            self.backgrounds = backgrounds
            self.requestId = requestId
    class Response:
        def __init__(self,requestId,*,image=None):
            self.image = image
            self.requestId = requestId
    def run(self):
        loop = asyncio.new_event_loop()
        while not self.stoprequest.isSet():
            try:
                request = self.input.get(True, 0.05)
                image = loop.run_until_complete(shop.generate(request.apikey,request.serverid,request.backgrounds))
                self.output.put(self.Response(request.requestId,image=image))
            except Queue.Empty:
                continue

class StatsImage(WorkerThread):
    class Request:
        def __init__(self,requestId,*,apikey=None,playername='',platform='pc',backgrounds=[],currentSeason=False):
            self.apikey = apikey
            self.playername = playername
            self.platform = platform
            self.backgrounds = backgrounds
            self.currentSeason = currentSeason
            self.requestId = requestId
    class Response:
        def __init__(self,requestId,*,image=None):
            self.image = image
            self.requestId = requestId
    def run(self):
        loop = asyncio.new_event_loop()
        while not self.stoprequest.isSet():
            try:
                request = self.input.get(True, 0.05)
                if request.currentSeason:
                    image = loop.run_until_complete(stats.generate_season(request.apikey,request.playername,request.platform,request.backgrounds))
                else:
                    image = loop.run_until_complete(stats.generate(request.apikey,request.playername,request.platform,request.backgrounds))
                self.output.put(self.Response(request.requestId,image=image))
            except Queue.Empty:
                continue

class UpcomingImage(WorkerThread):
    class Request:
        def __init__(self,requestId,*,apikey=None,serverid=None,backgrounds=[]):
            self.apikey = apikey
            self.serverid = serverid
            self.backgrounds = backgrounds
            self.requestId = requestId
    class Response:
        def __init__(self,requestId,*,image=None):
            self.image = image
            self.requestId = requestId
    def run(self):
        loop = asyncio.new_event_loop()
        while not self.stoprequest.isSet():
            try:
                request = self.input.get(True, 0.05)
                image = loop.run_until_complete(upcoming.generate(request.apikey,request.serverid,request.backgrounds))
                self.output.put(self.Response(request.requestId,image=image))
            except Queue.Empty:
                continue

class Shard(WorkerThread):
    def __init__(self,*,id=0,count=1,name=''):
        super().__init__()
        self.id = id
        self.count = count
        self.name = name
    def run(self):
        self.shard = bot.Shard(id=self.id,count=self.count,input=self.input,output=self.output)
        self.shard.run()

class ThreadController(threading.Thread):
    class Request:
        def __init__(self,*,id=0):
            self.id = id
    def __init__(self,threads=1):
        super().__init__()
        self.threads = Map()
        self.threadCount = threads
        self.stoprequest = threading.Event()
        self.reqNo = 0
    def run(self):
        self.createShards()
        for thread in self.threads:
            thread.start()
        while not self.stoprequest.isSet():
            for thread in self.threads:
                if isinstance(thread,WorkerThread):
                    request = thread.output.get(False)
                    if request is not None:
                        pass

    def createShards(self):
        for i in range(self.threadCount):
            name = 'shard_{0}'.format(i)
            self.threads.set(name,Shard(id=i,count=self.threadCount,name=name))

def isRequest(value):
    return isinstance(value,ThreadController.Request)

if __name__ == '__main__':
    controller = ThreadController(threads=3)
    controller.start()
