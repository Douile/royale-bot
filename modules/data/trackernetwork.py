import requests
from utils import strings

BASEURL = "https://api.fortnitetracker.com/v1"

class APIRequest():
    def __init__(self,key,endpoint,arguments={}):
        self.key = key
        self.endpoint = endpoint
        self.arguments = arguments
    def url(self):
        url = BASEURL + self.endpoint + self.parseArguments()
        return url
    def parseArguments(self):
        args = ""
        for a in self.arguments:
            args += strings.uriencode(a) + "=" + strings.uriencode(self.arguments[a]) + "&"
        if len(args) > 0:
            args = "?" + args
        return args
    def send(self):
        headers = {'TRN-Api-Key':self.key}
        self.response = APIResponse(requests.get(url=self.url(),headers=headers))
        return self.response
class StatsRequest(APIRequest):
    def __init__(self,key,name,platform="pc"):
        endpoint = "/profile/{0}/{1}".format(platform,name)
        super().__init__(key,endpoint,{})

class APIResponse():
    def __init__(self,response):
        self.headers = response.headers
        try:
            self.json = response.json()
        except ValueError:
            self.json = {}
        try:
            self.status = self.json['status']
        except KeyError:
            self.status = response.status_code
        self.ratelimitperminute = self.headers['X-RateLimit-Limit-minute']
        self.ratelimitremaining = self.headers['X-RateLimit-Remaining-minute']
        if self.status == 200:
            self.data = ProfileResponse(self.json)
        else:
            self.data = None
class ProfileResponse():
    def __init__(self,json={}):
        self.accountId = json['accountId']
        self.platformId = json['platformId']
        self.platformName = json['platformName']
        self.platformNameLong = json['platformNameLong']
        self.epicUserHandle = json['epicUserHandle']
        self.stats = {}
        if 'stats' in json:
            for id in json['stats']:
                self.stats[id] = StatsItem(id,json['stats'][id])
        self.lifetimestats = LifetimeStats(json['lifeTimeStats'])
class StatsItem():
    def __init__(self,id,json={}):
        self.id = id
        self.items = {}
        for id in json:
            self.items[id] = StatItem(id,json[id])
class StatItem():
    def __init__(self,id,json={}):
        self.id = id
        for type in json:
            value = json[type]
            if type == 'label':
                self.label = value
            elif type == 'field':
                self.field = value
            elif type == 'category':
                self.category = value
            elif type == 'valueDec':
                self.valueDec = value
            elif type == 'value':
                self.value = value
            elif type == 'rank':
                self.rank = value
            elif type == 'percentile':
                self.percentile = value
            elif type == 'displayValue':
                self.displayValue = value
class LifetimeStats():
    def __init__(self,json=[]):
        for i in range(0,len(json)):
            stat = json[i]['key']
            value = json[i]['value']
            if stat == 'Top 3':
                self.top3 = value
            elif stat == 'Top 5s':
            	self.top5s = value
            elif stat == 'Top 3s':
            	self.top3s = value
            elif stat == 'Top 6s':
            	self.top6s = value
            elif stat == 'Top 12s':
            	self.top12s = value
            elif stat == 'Top 25s':
            	self.top25s = value
            elif stat == 'Score':
            	self.score = value
            elif stat == 'Matches Played':
            	self.matchesplayed = value
            elif stat == 'Wins':
            	self.wins = value
            elif stat == 'Win%':
            	self.winpercent = value
            elif stat == 'Kills':
            	self.kills = value
            elif stat == 'K/d':
            	self.kdr = value
            elif stat == 'Kills Per Min':
            	self.killspermin = value
            elif stat == 'Time Played':
            	self.timeplayed = value
            elif stat == 'Avg Survival Time':
            	self.avgsurvivaltime = value
