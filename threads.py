import threading, Queue, asyncio
from imagegeneration import shop, stats, upcoming
import bot

class WorkerThread(threading.Thread):
    def __init__(self):
        super(WorkerThread, self).__init__()
        self.input = Queue.Queue()
        self.output = Queue.Queue()
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
    def run(self,*,id=0,count=1):
        self.shard = bot.Shard(id=id,count=count)
        self.shard.run()

class ThreadController(threading.Thread):
    def __init__(self,threads=1):
        super().__init__()
        self.threads = []
        self.threadCount = threads
    def run(self):
        for i in range(self.threadCount):
            self.threads.append(Shard(id=i,count=threadCount))
        for thread in self.threads:
            thread.start()

if __name__ == '__main__':
    controller = ThreadController(threads=2)
    controller.start()
