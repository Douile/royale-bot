import PIL.Image
import PIL.ImageFont
import PIL.ImageDraw
from datetime import datetime
from random import choice
from utils import arrays, integers, images
from math import ceil
import asyncio
from os.path import isfile
import logging

from dataretrieval import fnbr
from .shop import ItemImage

FONT = "assets/burbank.ttf"

class UpcomingImage:
    def __init__(self, size=200, padding=20, fontsize=40, rowsize=5, icount=5, background=None):
        self.size = size
        self.padding = padding
        self.fontsize = fontsize
        self.font = PIL.ImageFont.truetype(FONT,self.fontsize)
        self.fheight = self.font.getsize("Tp")[1]
        self.rows = ceil(icount/rowsize)
        self.rowsize = rowsize
        self.width = self.padding + self.size*rowsize + self.padding*rowsize
        self.height = self.padding*2 + self.fheight + self.size*self.rows + self.padding*self.rows
        self.background_generator = images.Background((self.width,self.height),color=(0,0,0,0))
        if type(background) is str:
            self.background_generator.url = background
    @asyncio.coroutine
    def generate(self,items):
        self.background = yield from self.background_generator.generate()
        yield from self.drawImages(items)
        yield from self.drawText()
        return self.background
    @asyncio.coroutine
    def drawImages(self, items):
        sets = arrays.split(items,self.rowsize)
        ctop = self.fheight+self.padding*2
        for set in sets:
            width = (len(set)*self.size)+((len(set)-1)*self.padding)
            cleft = self.padding
            for image in set:
                r = image.resize((self.size,self.size))
                logging.getLogger('upcoming-generator').debug('Item image at (%d,%d)',cleft,ctop)
                self.background.paste(r,(round(cleft),round(ctop)),r)
                cleft += self.size + self.padding
            ctop += self.size + self.padding
    @asyncio.coroutine
    def drawText(self):
        color = (255,255,255,255)
        text = 'Upcoming items'
        width = self.font.getsize(text)[0]
        left = round((self.background.width-width)/2)
        top = round(self.padding/2)
        draw = PIL.ImageDraw.Draw(self.background)
        draw.text((left,top),text,font=self.font,fill=color)

@asyncio.coroutine
def generate(data,backgrounds=[],serverid=None):
    items = []
    backupprice = 'https://image.fnbr.co/price/icon_vbucks.png'
    for item in data.data.items:
        if item.priceIconLink != 'false' and item.priceIconLink != False and item.priceIconLink != 'False':
            backupprice = item.priceIconLink
            priceIcon = item.priceIconLink
        else:
            priceIcon = backupprice
        if item.seen is not None:
            count = item.seen.occurrences
        else:
            count = -1
        if item.featured != '' and item.featured != False and item.featured != 'False':
            im = ItemImage(item.name,item.price,priceIcon,item.rarity,item.featured,512,count)
        elif item.icon != '' and item.icon != False and item.icon != 'False':
            im = ItemImage(item.name,item.price,priceIcon,item.rarity,item.icon,512,count) # i need to create a function for this
        elif item.png != '' and item.png != False and item.png != 'False':
            im = ItemImage(item.name,item.price,priceIcon,item.rarity,item.png,512,count)
        else:
            im = ItemImage(item.name,item.price,priceIcon,item.rarity,item.priceIconLink,512,count)
        items.append(im.out())
    if len(backgrounds) > 0:
        background = choice(backgrounds)
    else:
        background = None
    image_generator = UpcomingImage(size=300, padding=40, fontsize=40, rowsize=5, icount=len(items), background=background)
    image = yield from image_generator.generate(items)
    fname = 'upcoming.png'
    image.save(fname)
    return fname
@asyncio.coroutine
def getData(apikey):
    print("Getting upcoming data")
    req = fnbr.Upcoming(apikey)
    data = yield from req.send()
    return data
