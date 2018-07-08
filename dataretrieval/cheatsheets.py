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
    session = aiohttp.ClientSession(headers={'User-Agent':'RoyaleBot vX.X.X'})
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
    sheets = []
    kind = data.get('kind')
    if kind == 'Listing':
        items = data.get('data',{}).get('children',[])
        for container in items:
            if container.get('kind') == 't3':
                item = container.get('data',{})
                if item.get('subreddit') == 'FortNiteBR':
                    title = item.get('title')
                    print('Post in correct subreddit: {}'.format(title))
                    if strings.includes(title.lower(),'cheat sheet','challenges'):
                        print('Post title contains key words')
                        season = strings.num_after(title.lower(),'season')
                        week = strings.num_after(title.lower(),'week')
                        print('\tSeason: {}\n\tWeek: {}'.format(season,week))
                        if season is not None and week is not None:
                            image = None
                            images = item.get('preview',{}).get('images',[])
                            if len(images) > 0:
                                image = images[0].get('source',{}).get('url')
                            sheets.append(CheatSheet(title=title,season=season,week=week,image=image))
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
