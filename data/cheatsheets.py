import asyncio
import aiohttp
import logging
import traceback
from utils import strings

class CheatSheet:
    def __init__(self,*,title=None,season=0,week=0,image=None):
        self.title = title
        self.season = season
        self.week = week
        self.image = image
    def __str__(self):
        return 'Season {} Week {}   {}'.format(self.season,self.week,self.image)
    @property
    def has_image(self):
        image = False
        if self.image is not None:
            image = True
        return image

@asyncio.coroutine
def get_reddit_posts(user):
    url = 'http://api.reddit.com/user/{0}/submitted/?sort=new'.format(user)
    session = aiohttp.ClientSession(headers={'User-Agent':'RoyaleBot'})
    response = yield from session.get(url)
    json = None
    if response.status == 200:
        json = yield from response.json()
    else:
        response.raise_for_status()
    yield from session.close()
    return json

@asyncio.coroutine
def parse_cheat_sheets(data):
    session = aiohttp.ClientSession(headers={'User-Agent':'RoyaleBot'})
    sheets = []
    kind = data.get('kind')
    if kind == 'Listing':
        items = data.get('data',{}).get('children',[])
        for container in items:
            if container.get('kind') == 't3':
                item = container.get('data',{})
                if item.get('subreddit') == 'FortNiteBR':
                    title = item.get('title')
                    if strings.includes(title.lower(),'cheat sheet','challenges'):
                        season = strings.num_after(title.lower(),'season')
                        week = strings.num_after(title.lower(),'week')
                        if season is not None and week is not None:
                            image = None
                            def_image = item.get('url')
                            if def_image is not None:
                                response = yield from session.head(def_image)
                                if response.status == 200:
                                    image = def_image
                            if image is None:
                                images = item.get('preview',{}).get('images',[])
                                if len(images) > 0:
                                    for oimage in images:
                                        image_url = oimage.get('source',{}).get('url')
                                        if image_url is not None:
                                            response = yield from session.head(image_url)
                                            if response.status == 200:
                                                image = image_url
                                                break
                            sheets.append(CheatSheet(title=title,season=season,week=week,image=image))
    yield from session.close()
    return sheets

@asyncio.coroutine
def get_cheat_sheets():
    data = yield from get_reddit_posts('thesquatingdog')
    sheets = yield from parse_cheat_sheets(data)
    return sheets

@asyncio.coroutine
def debug_sheets():
    sheets = yield from get_cheat_sheets()
    for sheet in sheets:
        if sheet.has_image:
            print(sheet)
