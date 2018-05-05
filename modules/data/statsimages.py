from . import stats
from utils import integers, times
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import asyncio
import aiohttp
import random
from io import BytesIO

DEFAULT_SIZE = (1000,600)
DEFAULT_FONT = 'assets/burbank.ttf'
DEFAULT_COLOR = (255,255,255,170)

class Background:
    def __init__(self,color=None,url=None):
        if (color == None and url == None) or (color != None and url != None):
            raise RuntimeError('You must specify either color or url not both or neither.')
        if color != None:
            self.color = color
        elif url != None:
            self.url = url
        self.size = DEFAULT_SIZE
    @property
    def color(self):
        return self._color
    @color.setter
    def color(self,color):
        self._color = color
        self._url = None
    @property
    def url(self):
        return self._url
    @url.setter
    def url(self,url):
        self._url = url
        self._color = None
    @asyncio.coroutine
    def generate(self):
        image = None
        if self.color != None:
            image = PIL.Image.new('RGBA',self.size,color=self.color)
        elif self.url != None:
            image = yield from self.collectImage(self.url)
            image = yield from self.reCropImage(image,self.size)
        return image
    @staticmethod
    @asyncio.coroutine
    def collectImage(url):
        response = yield from aiohttp.get(url)
        content = yield from response.read()
        response.close()
        image = PIL.Image.open(BytesIO(content)).convert('RGBA')
        return image
    @staticmethod
    @asyncio.coroutine
    def reCropImage(image,size):
        if image.height / size[1] > image.width / size[0]:
            width = size[0]
            height = round(size[1] / image.width * image.height)
            image = image.resise((width,height))
            top = (size[1] - height)/2
            bottom = top + height
            image = image.crop((0,top,width,bottom))
        elif image.width / size[0] > image.height / size[1]:
            height = size[1]
            width = round(size[0] / image.height * image.width)
            image = image.resize((width,height))
            left = (size[0] - width)/2
            right = width + size[0]
            image = image.crop((left,0,right,height))
        elif image.width / size[0] == image.height / size[1]:
            image = image.resize(size)
        return image

class Overlay:
    def __init__(self,color=None):
        self.size = DEFAULT_SIZE
        if color == None:
            self.color = DEFAULT_COLOR
        else:
            self.color = color
    @asyncio.coroutine
    def generate(self,data):
        image = PIL.Image.new('RGBA',self.size,(0,0,0,0))
        padding_x = round(self.size[0]/20)
        padding_y = round(self.size[1]/20)
        size_x_small = padding_x*5
        size_x_large = padding_x*12
        size_y_small = padding_y*5
        size_y_large = padding_y*12
        overview = Overview((size_x_large,size_y_small))
        overview_image = yield from overview.generate(data.userdata,data.lifetime)
        image.paste(overview_image,(padding_x,padding_y),overview_image)
        performance = Performance((size_x_small,size_y_small))
        performance_image = yield from performance.generate(data.matches)
        image.paste(performance_image,(padding_x*2+size_x_large,padding_y),performance_image)
        main = Main((size_x_small+size_x_large+padding_x,size_y_large))
        main_image = yield from main.generate(data.stats)
        image.paste(main_image,(padding_x,padding_y*2+size_y_small),main_image)
        return image

class Overview:
    def __init__(self,size):
        self.size = size
        self.color = DEFAULT_COLOR
        self.padding = 15
    @asyncio.coroutine
    def generate(self,userdata,lifetimestats):
        lifetime = Map(lifetimestats)
        image = PIL.Image.new('RGBA',self.size,self.color)
        draw = PIL.ImageDraw.Draw(image)
        fontsize = round(self.size[1]/2)-self.padding*2
        font = PIL.ImageFont.truetype(DEFAULT_FONT,size=fontsize)
        font_small = PIL.ImageFont.truetype(DEFAULT_FONT,size=round(fontsize/2))
        draw.text((self.padding,self.padding),userdata.name,fill=(255,255,255,255),font=font)
        platformsize = font.getsize(userdata.platform)[0]
        platformleft = self.size[0]-(self.padding+platformsize)
        draw.text((platformleft,self.padding),userdata.platform,fill=(255,255,255,255),font=font)
        statstext = 'KD {kd} WINS {wins} '.format_map(lifetime)
        draw.text((self.padding,fontsize+self.padding*3),statstext,fill=(255,255,255,255),font=font)
        extra = 'MATCHES {matches} WIN% {win_percent}\nSCORE {score}'.format_map(lifetime)
        extrasize = font_small.getsize(extra.split('\n')[0])
        extrasize = (extrasize[0],extrasize[1]*2 + 5)
        extraleft = self.size[0]-(extrasize[0]+self.padding)
        extratop = self.size[1]-(extrasize[1]+self.padding)
        draw.multiline_text((extraleft,extratop),extra,fill=(255,255,255,255),font=font_small,spacing=5)
        return image

class Performance:
    def __init__(self,size):
        self.size = size
        self.color = DEFAULT_COLOR
        self.padding = 20
    @asyncio.coroutine
    def generate(self,matches):
        image = PIL.Image.new('RGBA',self.size,self.color)
        draw = PIL.ImageDraw.Draw(image)
        font = PIL.ImageFont.truetype(DEFAULT_FONT,size=round(self.padding/2))
        fg = (255,255,255,255)
        draw.line([(self.padding,self.padding),(self.padding,self.size[1]-self.padding)],fill=fg,width=2)
        draw.line([(self.padding,self.size[1]-self.padding),(self.size[0]-self.padding,self.size[1]-self.padding)],fill=fg,width=2)
        intervals = len(matches)
        if intervals > 0:
            kds = []
            for match in matches:
                kds.append(match.kd)
            matches.reverse()
            lowest = integers.lowest(*kds)
            highest = integers.highest(*kds)
            range = highest-lowest
            total_size = self.size[0]-self.padding*2
            interval_size = round(total_size/(intervals+1))
            left = self.padding+interval_size
            bottom = self.size[1]-self.padding-5
            height = self.size[1]-self.padding*2-5
            text_top = round(self.size[1]-self.padding/4)
            last_pos = None
            now = times.epoch_now()/60
            count = 1
            for match in matches:
                size_y = (match.kd-lowest)*(height/range)
                pos = (left,round(bottom-size_y))
                tl = (pos[0]-2,pos[1]-2)
                br = (pos[0]+2,pos[1]+2)
                draw.ellipse([tl,br],fill=fg)
                if last_pos != None:
                    draw.line([last_pos,pos],fill=fg,width=2)
                time = times.isotime(match.time).timestamp()
                mins = '-'+str(round(now-(time/60)))
                width = font.getsize(mins)[0]
                if count == 1 or count == intervals:
                    draw.text((round(left-width/2),round(text_top-font.getsize('0')[1])),mins,fill=fg,font=font)
                last_pos = pos
                left += interval_size
                count += 1
        return image

class Main:
    def __init__(self,size):
        self.size = size
        self.color = DEFAULT_COLOR
        self.padding = 15
    @asyncio.coroutine
    def generate(self,stats):
        image = PIL.Image.new('RGBA',self.size,self.color)
        draw = PIL.ImageDraw.Draw(image)
        return image
class Stats:
    def __init__(self):
        self.background = Background(color=(0,0,0,0))
        self.overlay = Overlay()
    def setBackground(color=None,url=None):
        if url != None:
            self.background.url = url
        if color != None:
            self.background.color = color
    @asyncio.coroutine
    def generate(self,data):
        background = yield from self.background.generate()
        overlay = yield from self.overlay.generate(data)
        background.paste(overlay,(0,0),overlay)
        return background

class StatsData:
    def __init__(self,data):
        if type(data) is dict:
            self.userdata = self.UserData(data)
            self.lifetime = self.LifetimeStats(data.get('lifeTimeStats',[]))
            self.matches = self.Matches(data.get('recentMatches',[]))
            self.stats = self.Stats(data.get('stats',{}))
            # p2 solo p10 duo p9 squads
        else:
            raise RuntimeError('You must pass a dict argument')
    class UserData:
        def __init__(self,data):
            self.account_id = data.get('accountId','')
            self.platform_id = data.get('platformId',0)
            self.platform = data.get('platformNameLong','')
            self.name = data.get('epicUserHandle','')
        def __iter__(self):
            yield 'account_id', self.account_id
            yield 'platform_id', self.platform_id
            yield 'platform', self.platform
            yield 'name', self.name
    class LifetimeStats:
        def __init__(self,data):
            if type(data) is list:
                for item in data:
                    key = item.get('key','')
                    value = item.get('value','')
                    if key == 'Top 3':
                        self.top_3 = value
                    elif key == 'Top 5s':
                        self.top_5s = value
                    elif key == 'Top 3s':
                        self.top_3s = value
                    elif key == 'Top 6s':
                        self.top_6s = value
                    elif key == 'Top 12s':
                        self.top_12s = value
                    elif key == 'Top 25s':
                        self.top_25s = value
                    elif key == 'Score':
                        self.score = value
                    elif key == 'Matches Played':
                        self.matches = value
                    elif key == 'Wins':
                        self.wins = value
                    elif key == 'Kills':
                        self.kills = value
                    elif key == 'K/d':
                        self.kd = value
            if self.matches != None and self.wins != None:
                self.win_percent = round((int(self.wins)/int(self.matches))*100,2)
        def __iter__(self):
            yield 'score', self.score
            yield 'matches', self.matches
            yield 'wins', self.wins
            yield 'kills', self.kills
            yield 'kd', self.kd
            yield 'win_percent', self.win_percent
    class Matches(list):
        def __init__(self,data):
            if type(data) is list:
                for match in data:
                    self.append(self.Match(match))
        class Match:
            def __init__(self,data):
                self.id = data.get('id',0)
                self.playlist = data.get('playlist','')
                self.kills = data.get('kills',0)
                self.matches = data.get('matches',0)
                self.score = data.get('score',0)
                self.platform = data.get('platform',0)
                self.time = data.get('dateCollected','')
                self.wins = data.get('top1',0)
                if self.matches != None and self.kills != None and self.wins != None:
                    if self.matches == self.wins:
                        self.kd = self.kills
                    else:
                        self.kd = self.kills/(self.matches-self.wins)
    class Stats:
        def __init__(self,data):
            solo = data.get('p2',None)
            duo = data.get('p10',None)
            squad = data.get('p9',None)
            if solo != None:
                self.solo = self.Stat(solo)
            if duo != None:
                self.duo = self.Stat(duo)
            if squad != None:
                self.squad = self.Stat(squad)
        class Stat:
            def __init__(self,data):
                self.score = self.getStat(data,'score')
                self.kd = self.getStat(data,'kd')
                self.win_percent = self.getStat(data,'winRatio')
                self.matches = self.getStat(data,'matches')
                self.kills = self.getStat(data,'kills')
                self.kills_per_game = self.getStat(data,'kpg')
                self.score_per_match = self.getStat(data,'scorePerMatch')
            @staticmethod
            def getStat(data,key):
                d = data.get(key,None)
                if d != None:
                    o = d.get('value','')
                else:
                    o = ''
                return o

class Map(dict):
    def __missing__(self, key):
        return key

@asyncio.coroutine
def generate(KEY_TN,player,platform,backgrounds=[]):
    print(backgrounds)
    stats_data = yield from stats.stats(KEY_TN,player,platform)
    if stats_data['status'] == 200:
        stat_data = StatsData(stats_data)
        statsimage = Stats()
        if len(backgrounds) > 0:
            url = random.choice(backgrounds)
            print(url)
            statsimage.background.url = url
        image = yield from statsimage.generate(stat_data)
    else:
        image == None
    return image
