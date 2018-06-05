import aiohttp
import asyncio
from urllib.parse import quote_plus
import re
import bs4

# constants
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'

BASEURL = "https://fnbr.co/api"
VALID_IMAGE_TYPES = ['emote','glider','emoji','loading','outfit','pickaxe','skydive','umbrella','misc']
VALID_IMAGE_LIMIT_MIN = 1
VALID_IMAGE_LIMIT_MAX = 15

NONE_TYPE = "none"
ERROR_TYPE = "error"
STATS_TYPE = "stats"
IMAGE_TYPE = "image"
SHOP_TYPE = "shop"
LIST_TYPE = "list"
SEEN_TYPE = "seen"

CSRF_TOKEN = None
# requests
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
            args += uriencode(a) + "=" + uriencode(self.arguments[a]) + "&"
        if len(args) > 0:
            args = "?" + args
        return args
    @asyncio.coroutine
    def send(self):
        client = aiohttp.ClientSession()
        headers = {'x-api-key':self.key}
        response_data = yield from client.get(url=self.url(),headers=headers)
        json = yield from response_data.json()
        self.response = APIResponse(response_data, json)
        yield from client.close()
        return self.response
class Images(APIRequest):
    def __init__(self,key,search=None,type=None,limit=None):
        super().__init__(key,"/images",{})
        self.setSearch(search)
        self.setType(type)
        self.setLimit(limit)
    def setSearch(self,search=""):
        set = False
        if type(search) is str:
            self.arguments['search'] = search
            set = True
        return set
    def setType(self,itype=""):
        set = False
        if type(itype) is str:
            itype = itype.lower()
            if type in VALID_IMAGE_TYPES:
                self.arguments['type'] = itype
                set = True
        return set
    def setLimit(self,limit=1):
        set = False
        if type(limit) is int:
            self.arguments['limit'] = bounds(limit,VALID_IMAGE_LIMIT_MIN,VALID_IMAGE_LIMIT_MAX)
            set = True
        return set
class Shop(APIRequest):
    def __init__(self,key):
        super().__init__(key,"/shop",{})
class Stat(APIRequest):
    def __init__(self,key):
        super().__init__(key,"/stats",{})
class ItemList(APIRequest):
    def __init__(self):
        """Unauthenticated method to find every item. Only returns name,id and type"""
        self.urltouse = "https://fnbr.co/list"
    def url(self):
        return self.urltouse
    @asyncio.coroutine
    def send(self):
        client = aiohttp.ClientSession()
        response_data = yield from client.get(url=self.url())
        json = yield from response_data.json()
        self.response = APIResponse(response_data, json)
        yield from client.close()
        return self.response
class Seen(APIRequest):
    def __init__(self, id=''):
        super().__init__(None,"/seen/",{})
        self.item_id = id
    def url(self):
        return BASEURL + self.endpoint + self.item_id + self.parseArguments()
    @asyncio.coroutine
    def send(self):
        client = aiohttp.ClientSession(headers=[('User-Agent',USER_AGENT)])
        if CSRF_TOKEN is None:
            main = yield from client.get('https://fnbr.co')
            if main.status == 200:
                text = yield from main.text()
                html = bs4.BeautifulSoup(text,'html.parser')
                tags = html.find_all('meta',{'name':'csrf-token'})
                if len(tags) > 0:
                	CSRF_TOKEN = tags[0].attrs['content']
            main.close()
            print(CSRF_TOKEN)
        json = None
        response = None
        if CSRF_TOKEN is not None:
            url = self.url()
            headers = {'csrf-token':CSRF_TOKEN}
            response = yield from client.get(url,headers=headers)
            json = yield from response.json()
            response.close()
        yield from client.close()
        self.response = APIResponse(response, json)
        return self.response
class ShopAndSeen:
    def __init__(self, apikey):
        self.key = apikey
    @asyncio.coroutine
    def send(self):
        shop = Shop(self.key)
        data = yield from shop.send()
        if data.type == SHOP_TYPE:
            for item in data.data.daily+data.data.featured:
                seen = Seen(item.id)
                seen_data = yield from seen.send()
                item.seen = seen_data.data
        return data
# responses
class APIResponse():
    def __init__(self,response,json):
        self.headers = response.headers
        self.json = json
        try:
            self.status = self.json['status']
        except KeyError:
            self.status = response.status
        url = response.url
        if self.status != 200:
            self.type = ERROR_TYPE
            try:
                self.error = self.json['error']
            except KeyError:
                self.error = response.reason
        elif '/images' in url:
                self.type = IMAGE_TYPE
                self.data = ImageResponse(self.json)
        elif '/shop' in url:
                self.type = SHOP_TYPE
                self.data = ShopResponse(self.json)
        elif '/stats' in url:
            self.type = STATS_TYPE
            self.data = StatResponse(self.json)
        elif '/seen' in url:
            self.type = SEEN_TYPE
            self.data = SeenResponse(self.json)
        elif '/list' in url:
            self.type = LIST_TYPE
            self.data = ItemListResponse(response.text)
        else:
            self.type = NONE_TYPE
class ShopResponse():
    def __init__(self,json={}):
        self.featured = []
        for i in range(0,len(json['data']['featured'])):
            self.featured.append(Item(json['data']['featured'][i]))
        self.daily = []
        for i in range(0,len(json['data']['daily'])):
            self.daily.append(Item(json['data']['daily'][i]))
        self.date = json['data']['date']
class StatResponse():
    def __init__(self,json={}):
        self.totalCosmetics = json['totalCosmetics']
        self.matrix = []
        if 'matrix' in json:
            for i in range(0,len(json['matrix'])):
                self.matrix.append(StatItem(json['matrix'][i]))
class ImageResponse():
    def __init__(self,json={}):
        self.results = []
        for i in range(0,len(json['data'])):
            self.results.append(Item(json['data'][i]))
class ItemListResponse():
    def __init__(self,text=""):
        self.items = []
        f = re.DOTALL|re.MULTILINE
        for item in re.finditer('<tr>(.*?)<\/tr>',text,flags=f):
            str = item.group(0).replace("\n","")
            name = re.findall('<td>(.*?)<\/td>',str)
            if len(name) > 0:
                name = name[0]
                icon = re.findall('src="https://image.fnbr.co/(.*?)/icon.png"',str)[0]
                type = re.findall('<td class="capital">(.*?)<\/td>',str)[0]
                rarity = re.findall('<td class="\w capital">(.*?)<\/td>',str)
                js = {'name':name,'type':type,'rarity':rarity,'images':{'icon':icon}}
                self.items.append(Item(js))
class SeenResponse():
    def __init__(self,json={}):
        data = json.get('data',{})
        self.lastSeen = data.get('lastSeen')
        self.firstSeen = data.get('firstSeen')
        self.occurrences = data.get('occurrences')
        if self.occurrences is not None:
            if self.occurrences < 2:
                self.new = True
            else:
                self.new = False
        else:
            self.new = False

class Item():
    def __init__(self,json={}):
        self.id = self.load('id',json)
        self.name = self.load('name',json)
        self.price = self.load('price',json)
        self.priceIcon = self.load('priceIcon',json)
        self.priceIconLink = self.load('priceIconLink',json)
        self.rarity = self.load('rarity',json)
        self.type = self.load('type',json)
        self.readableType = self.load('readableType',json)
        if 'images' in json:
            self.icon = self.load('icon',json['images'])
            self.png = self.load('png',json['images'])
            self.gallery = self.load('gallery',json['images'])
            self.featured = self.load('featured',json['images'],False)
        self.seen = None
    def load(self,name,json,default=""):
        if name in json:
            value =  json[name]
        else:
            value = default
        return value
class StatItem():
    def __init__(self,json={}):
        self.type = self.load('type',json)
        self.rarity = []
        if 'rarity' in json:
            for i in range(0,len(json['rarity'])):
                self.rarity.append(StatRarity(json['rarity'][i]))
    def load(self,name,json,default=""):
        if name in json:
            value =  json[name]
        else:
            value = default
        return value
class StatRarity():
    def __init__(self,json={}):
        self.rarity = json['rarity']
        self.count = json['count']

# functions
def bounds(value,min,max):
    if value < min:
        value = min
    elif value > max:
        value = max
    return value
def uriencode(string):
    if type(string) is int:
        string = str(string)
    return quote_plus(bytes(string,"utf-8"))
