class ThreadRequest:
    def __init__(self,*,dest=None,source=None,requestId=None):
        self.dest = dest
        self.source = source
        self.requestId = requestId

class ShopImage:
    class Request(ThreadRequest):
        def __init__(self,requestId,*,apikey=None,serverid=None,backgrounds=[]):
            super().__init__(dest='shop',requestId=requestId)
            self.apikey = apikey
            self.serverid = serverid
            self.backgrounds = backgrounds
    class Response(ThreadRequest):
        def __init__(self,to,requestId,*,image=None):
            super().__init__(dest=to,requestId=requestId)
            self.image = image

class StatsImage:
    class Request(ThreadRequest):
        def __init__(self,requestId,*,apikey=None,playername='',platform='pc',backgrounds=[],currentSeason=False):
            super().__init__(dest='stats',requestId=requestId)
            self.apikey = apikey
            self.playername = playername
            self.platform = platform
            self.backgrounds = backgrounds
            self.currentSeason = currentSeason
            self.requestId = requestId
    class Response(ThreadRequest):
        def __init__(self,to,requestId,*,image=None):
            super().__init__(dest=to,requestId=requestId)
            self.image = image

class UpcomingImage:
    class Request(ThreadRequest):
        def __init__(self,requestId,*,apikey=None,serverid=None,backgrounds=[]):
            super().__init__(dest='upcoming',requestId=requestId)
            self.apikey = apikey
            self.serverid = serverid
            self.backgrounds = backgrounds
    class Response(ThreadRequest):
        def __init__(self,to,requestId,*,image=None):
            super().__init__(dest=to,requestId=requestId)
            self.image = image
