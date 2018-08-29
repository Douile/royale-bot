import threading, queue, asyncio
from imagegeneration import shop, stats, upcoming
import bot
import transportDefs

class Queue(queue.Queue):
    def find(self, test):
        """ Provide a test function to check all items in queue """
        i = 0
        for item in self.queue:
            if test(item):
                i += 1
        return i
    def get(self,requestId):
        for item in self.queue:
            if isinstance(item,transportDefs.ThreadRequest):
                if item.requestId == requestId:
                    self.queue.remove(item)
                    return item
        return None

class WorkerThread(threading.Thread):
    def __init__(self):
        super(WorkerThread, self).__init__()
        self.input = Queue()
        self.output = Queue()
        self.stoprequest = threading.Event()

class ShopImage(WorkerThread):
    def run(self):
        loop = asyncio.new_event_loop()
        while not self.stoprequest.isSet():
            try:
                request = self.input.get(True, 0.05)
                if isinstance(request,transportDefs.ShopImage.Request):
                    image = loop.run_until_complete(shop.generate(request.apikey,request.serverid,request.backgrounds))
                    self.output.put(transportDefs.ShopImage.Response(request.source,request.requestId,image=image))
            except queue.Empty:
                continue

class StatsImage(WorkerThread):
    def run(self):
        loop = asyncio.new_event_loop()
        while not self.stoprequest.isSet():
            try:
                request = self.input.get(True, 0.05)
                if isinstance(request,transportDefs.StatsImage.Request):
                    if request.currentSeason:
                        image = loop.run_until_complete(stats.generate_season(request.apikey,request.playername,request.platform,request.backgrounds))
                    else:
                        image = loop.run_until_complete(stats.generate(request.apikey,request.playername,request.platform,request.backgrounds))
                    self.output.put(transportDefs.StatsImage.Response(request.source,request.requestId,image=image))
            except queue.Empty:
                continue

class UpcomingImage(WorkerThread):
    def run(self):
        loop = asyncio.new_event_loop()
        while not self.stoprequest.isSet():
            try:
                request = self.input.get(True, 0.05)
                if isinstance(request,transportDefs.UpcomingImage.Request):
                    image = loop.run_until_complete(upcoming.generate(request.apikey,request.serverid,request.backgrounds))
                    self.output.put(transportDefs.UpcomingImage.Response(request,source,request.requestId,image=image))
            except queue.Empty:
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
        self.threads = {}
        self.threadCount = threads
        self.stoprequest = threading.Event()
        self.reqNo = 0
    def run(self):
        self.createShards()
        self.createWorkers()
        for threadName in self.threads:
            thread = self.threads[threadName]
            thread.start()
        while not self.stoprequest.isSet():
            for threadName in self.threads:
                thread = self.threads[threadName]
                if isinstance(thread,WorkerThread):
                    try:
                        request = thread.output.get(False)
                    except queue.Empty:
                        request = None
                    if request is not None:
                        if request.to in self.threads:
                            request.from = threadName
                            self.threads[request.to].input.put(request)

    def createShards(self):
        for i in range(self.threadCount):
            name = 'shard_{0}'.format(i)
            self.threads[name] = Shard(id=i,count=self.threadCount,name=name)
    def createWorkers(self):
        threadMap = {
            'shop': ShopImage(),
            'stats': StatsImage(),
            'upcoming': UpcomingImage()
        }
        for name in threadMap:
            self.threads[name] = threadMap[name]
        del threadMap


def isRequest(value):
    return isinstance(value,ThreadController.Request)

if __name__ == '__main__':
    controller = ThreadController(threads=2)
    controller.start()
