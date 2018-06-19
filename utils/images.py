import math
import asyncio
import aiohttp
from io import BytesIO
import PIL.Image
from os.path import isfile
from .times import morning
from random import choice
import traceback
import logging

def radial_gradient(draw,width,height,color_inner,color_outer): # will overite everything in image
    """Creates a radial gradient on an image. Might be slow"""
    alpha = False
    if len(color_inner) == 4 and len(color_outer) == 4:
        alpha = True
    for x in range(width):
        for y in range(height):
            dToE = math.sqrt((x -width/2) ** 2 + (y - height/2) ** 2)
            dToE = float(dToE) / (math.sqrt(2) * width/2)
            r = round(color_inner[0] * dToE + color_outer[0] * (1-dToE))
            g = round(color_inner[1] * dToE + color_outer[1] * (1-dToE))
            b = round(color_inner[2] * dToE + color_outer[2] * (1-dToE))
            if alpha:
                a = round(color_inner[3] * dToE + color_outer[3] * (1-dToE))
                color = (r,g,b,a)
            else:
                color = (r,g,b)
            draw.point((x,y),fill=color)
def darken(color,alpha):
    """Darkens a color to specified alpha"""
    return (color[0],color[1],color[2],alpha)
class Background:
    def __init__(self,size,color=None,url=None):
        if (color == None and url == None) or (color != None and url != None):
            raise RuntimeError('You must specify either color or url not both or neither.')
        if color != None:
            self.color = color
        elif url != None:
            self.url = url
        self.size = size
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
            try:
                image = yield from self.collectImage(self.url)
                image = yield from self.reCropImage(image,self.size)
            except:
                error = traceback.format_exc()
                logging.getLogger('bg-generator').error('Error collecting image: %s', error)
                image = PIL.Image.new('RGBA',self.size,color=(0,0,0,0))
        return image
    @staticmethod
    @asyncio.coroutine
    def collectImage(url):
        session = aiohttp.ClientSession()
        response = yield from session.get(url,headers={'Accept':'image/*'})
        content = yield from response.read()
        response.close()
        yield from session.close()
        image = PIL.Image.open(BytesIO(content)).convert('RGBA')
        return image
    @staticmethod
    @asyncio.coroutine
    def reCropImage(image,size):
        logger = logging.getLogger('bg-generator')
        rw = image.width / size[0]
        rh = image.height / size[1]
        if rh > rw:
            nh = round(image.height / rw)
            nw = size[0]
        else:
            nw = round(image.width / rh)
            nh = size[1]
        logger.debug('Resized background o:(%d,%d) r:(%d,%d) n:(%d,%d)',image.width,image.height,rw,rh,nw,nh)
        image = image.resize((nw,nh))
        if image.width > size[0]:
            left = round((image.width - size[0]) / 2)
            right = left + size[0]
            logger.debug('Cropped horizontal ow: %d left: %d right: %d',image.width,left,right)
            image = image.crop((left,0,right,image.height))
        if image.height > size[1]:
            top = round((image.height - size[1]) / 2)
            bottom = top + size[1]
            logger.debug('Cropped vertical oh: %d top: %d bottom: %d',image.height,top,bottom)
            image = image.crop((0,top,image.width,bottom))
        return image

@asyncio.coroutine
def daily_cache_generator(generator,serverid,backgrounds,basename,*genargs): # improve efficiency
    filename_overlay = '{0}-{1}.png'.format(basename,round(morning()))
    if isfile(filename_overlay):
        overlay = PIL.Image.open(filename_overlay)
    else:
        overlay = yield from generator(*genargs)
        overlay.save(filename_overlay)
    if len(backgrounds) > 0:
        filename_server = '{0}-{1}.png'.format(filename_overlay[:-4],serverid)
        if isfile(filename_server):
            filename_final = filename_server
        else:
            background = choice(backgrounds)
            background_generator = Background((overlay.width,overlay.height),url=background)
            output = yield from background_generator.generate()
            output.paste(overlay,(0,0),overlay)
            output.save(filename_server)
            filename_final = filename_server
    else:
        filename_final = filename_overlay
    return filename_final
