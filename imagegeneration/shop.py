import PIL.Image
import PIL.ImageFont
import PIL.ImageDraw
from io import BytesIO
import requests
from datetime import datetime
from random import choice
from utils import arrays, integers, images
import asyncio
from os.path import isfile

from dataretrieval import fnbr

FONT = "assets/burbank.ttf"
NEW_IMG = "assets/new.png"


class ShopImage:
    def __init__(self, size=200, padding=20, fontsize=40, rowsize=3, fcount=2, dcount=6, date="", background=None):
        self.size = size
        self.padding = padding
        self.fontsize = fontsize
        self.font = PIL.ImageFont.truetype(FONT,self.fontsize)
        self.fheight = self.font.getsize("Tp")[1]
        self.frows = (fcount+(fcount%2))/2
        self.drows = (dcount+(dcount%2))/2
        self.rows = 1
        if self.frows > self.drows:
            self.rows = self.frows
        else:
            self.rows = self.drows
        self.height = round(self.padding*2 + self.padding*self.rows + self.fheight*2 + self.size*self.rows)
        self.width = round(self.padding*5 + self.size*4)
        self.background_generator = images.Background((self.width,self.height),color=(0,0,0,0))
        if type(background) is str:
            self.background_generator.url = background
        self.datetext = date
    @asyncio.coroutine
    def setFeatured(self, images):
        top = self.padding*2 + self.fheight*2
        left = self.padding
        yield from self.drawImages(left,top,images)
    @asyncio.coroutine
    def setDaily(self, images):
        top = self.padding*2 + self.fheight*2
        left = self.padding*3 + self.size*2
        yield from self.drawImages(left,top,images)
    @asyncio.coroutine
    def drawImages(self,left,top,images):
        sets = arrays.split(images,2)
        ctop = top
        for set in sets:
            width = (len(set)*self.size)+((len(set)-1)*self.padding)
            cleft = left
            for image in set:
                r = image.resize((self.size,self.size))
                print('Image at ',cleft,ctop)
                self.background.paste(r,(round(cleft),round(ctop)),r)
                cleft += self.size + self.padding
            ctop += self.size + self.padding
    @asyncio.coroutine
    def drawText(self):
        color = (255,255,255,255)
        draw = PIL.ImageDraw.Draw(self.background)
        top = round(self.padding/2)
        left = round((self.width-self.font.getsize(self.datetext)[0])/2)
        draw.text((left,top),self.datetext,font=self.font,fill=color)
        top = round(self.fheight + self.padding*1.5)
        left = round((self.width/2-self.font.getsize("Featured")[0])/2)
        draw.text((left,top),"Featured",font=self.font,fill=color)
        left = round((self.width/2)+(self.width/2-self.font.getsize("Daily")[0])/2)
        draw.text((left,top),"Daily",font=self.font,fill=color)
    @asyncio.coroutine
    def save(self,name):
        self.background.save(name)
    @asyncio.coroutine
    def generate(self,featured,daily,name):
        self.background = yield from self.background_generator.generate()
        yield from self.setFeatured(featured)
        yield from self.setDaily(daily)
        yield from self.drawText()
        return self.background
class ItemImage:
    def __init__(self,itemname,itemprice,itempriceimage,itemrarity,itemimageurl,size,count=0):
        self.size = size
        color = (255,255,255,0)
        if itemrarity == "uncommon":
            color = (56, 121, 39, 255)
            gradient = ((96,170,58,255),(23,81,23,255))
            background = 'assets/fortnite_uncommon.png'
        elif itemrarity == "rare":
            color = (61,171,245,255)
            gradient = ((73,172,242,255),(20,57,119,255))
            background = 'assets/fortnite_rare.png'
        elif itemrarity == "epic":
            color = (199,81,248,255)
            gradient = ((177,91,226,255),(75,36,131,255))
            background = 'assets/fortnite_epic.png'
        elif itemrarity == "legendary":
            color = (230,126,34,255)
            gradient = ((211,120,65,255),(120,55,29,255))
            background = 'assets/fortnite_legendary.png'
        try:
            self.background = PIL.Image.open(background)
            if self.background.width != self.size or self.background.height != self.size:
                self.background.resize(self.size)
        except IOError:
            self.background = PIL.Image.new("RGBA",(self.size,self.size),color)
            draw = PIL.ImageDraw.Draw(self.background)
            images.radial_gradient(draw,self.size,self.size,gradient[1],gradient[0])
        finally:
            draw = PIL.ImageDraw.Draw(self.background)
        fontsize = round(self.size/10)
        largefont = PIL.ImageFont.truetype(FONT,fontsize+10)
        smallfont = PIL.ImageFont.truetype(FONT,fontsize-10)
        largeheight = largefont.getsize("Test")[1]
        smallheight = smallfont.getsize("test")[1]
        textwidth = largefont.getsize(itemname)[0]
        left = round((self.size - textwidth) / 2)
        top = round(self.size - largeheight - smallheight - 15)
        imagesize = round(self.size - largeheight - smallheight - 10)
        imageleft = round((self.size-imagesize)/2)
        item = createImageFromUrl(itemimageurl).resize((self.size,self.size))
        self.background.paste(item,(0,0),item)
        self.darkenRect(draw,(0,top),(self.size,self.size),35)
        self.round(25)
        self.borderedText(draw,(left,top),itemname,largefont,(255,255,255),(0,0,0))
        textwidth = 10 + smallheight + smallfont.getsize(itemprice)[0]
        left = round((self.size - textwidth) / 2)
        top = round(top + largeheight + 5)
        price = createImageFromUrl(itempriceimage).resize((smallheight,smallheight))
        self.background.paste(price,(left,top),price)
        left = round(left +smallheight + 5)
        self.borderedText(draw,(left,top),itemprice,smallfont,(255,255,255),(0,0,0))
        if count > 0:
            if count == 1:
                count = 'NEW'
            countimg = CountImage(count).out()
            x = self.background.width - countimg.width - 10
            y = 10
            self.background.paste(countimg,(x,y),countimg)
    def borderedText(self,draw,pos,text,font,textcolor=(255,255,255),bordercolor=(0,0,0)):
        draw.text(pos,text,font=font,fill=textcolor)
    def round(self,size):
        cornertopleft = self.corner(size,self.background.getpixel((1,1)))
        cornertopright = self.corner(size,self.background.getpixel((self.size-2,1))).rotate(270)
        cornerbottomleft = self.corner(size,self.background.getpixel((1,self.size-2))).rotate(90)
        cornerbottomright = self.corner(size,self.background.getpixel((self.size-2,self.size-2))).rotate(180)
        self.background.paste(cornertopleft,(0,0))
        self.background.paste(cornertopright,(self.size-size,0))
        self.background.paste(cornerbottomleft,(0,self.size-size))
        self.background.paste(cornerbottomright,(self.size-size,self.size-size))
    def corner(self,size,fill):
        corner = PIL.Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = PIL.ImageDraw.Draw(corner)
        draw.pieslice((0, 0, size * 2, size * 2), 180, 270, fill=fill)
        return corner
    def sizedif(self,font1,font2,text): # obselete ^ bordered text
        size1 = font1.getsize(text)
        size2 = font2.getsize(text)
        return (size1[0]-size2[0],size1[1]-size2[1])
    def darkenRect(self,draw,start,end,amount=25):
        for x in range(start[0],end[0]):
            for y in range(start[1],end[1]):
                color = self.background.getpixel((x,y))
                r = integers.min(color[0]-amount,0)
                g = integers.min(color[1]-amount,0)
                b = integers.min(color[2]-amount,0)
                a = color[3]
                color = (r,g,b,a)
                draw.point((x,y),fill=color)
    def out(self):
        return self.background

class CountImage:
    def __init__(self, count):
        red = (255,0,0,255)
        white = (255,255,255,255)
        size = (50,50)
        count = str(count)
        font = PIL.ImageFont.truetype(FONT, 36)
        textsize = font.getsize(count)
        if textsize[0] > size[0]-4:
            size = (textsize[0]+4,size[1])
        self.background = PIL.Image.new('RGBA', size, (0,0,0,0))
        draw = PIL.ImageDraw.Draw(self.background)
        draw.ellipse([(0,0),self.background.size],fill=red)
        left = round((self.background.width-textsize[0])/2)
        top = round((self.background.height-textsize[1])/2)
        draw.text((left,top),count,fill=white,font=font)
    def out(self):
        return self.background

# functions
def createImageFromContent(content):
    image = PIL.Image.open(BytesIO(content)).convert("RGBA")
    return image

def createImageFromUrl(url):
    resp = requests.get(url)
    return createImageFromContent(resp.content)

# generate
@asyncio.coroutine
def generate(shopdata,backgrounds=[],serverid=None):
    print("Generating image")
    featured = []
    daily = []
    time = getTime(shopdata.data.date)
    date = time.strftime("%A %d %B")
    fname = filename(time)
    if isfile(fname):
        overlay = PIL.Image.open(fname)
    else:
        backupprice = 'https://image.fnbr.co/price/icon_vbucks.png'
        for item in shopdata.data.featured:
            if item.priceIconLink != 'false' and item.priceIconLink != False and item.priceIconLink != 'False':
                backupprice = item.priceIconLink
                priceIcon = item.priceIconLink
            else:
                priceIcon = backupprice
            count = item.seen.occurrences
            if item.icon != '' and item.icon != False and item.icon != 'False':
                im = ItemImage(item.name,item.price,priceIcon,item.rarity,item.icon,512,count) # i need to create a function for this
            elif item.png != '' and item.png != False and item.png != 'False':
                im = ItemImage(item.name,item.price,priceIcon,item.rarity,item.png,512,count)
            else:
                im = ItemImage(item.name,item.price,priceIcon,item.rarity,item.priceIconLink,512,count)
            featured.append(im.out())
        for item in shopdata.data.daily:
            if item.priceIconLink != 'false' and item.priceIconLink != False and item.priceIconLink != 'False':
                backupprice = item.priceIconLink
                priceIcon = item.priceIconLink
            else:
                priceIcon = backupprice
            count = item.seen.occurrences
            if item.icon != '' and item.icon != False and item.icon != 'False':
                im = ItemImage(item.name,item.price,priceIcon,item.rarity,item.icon,512,count)
            elif item.png != '' and item.png != False and item.png != 'False':
                im = ItemImage(item.name,item.price,priceIcon,item.rarity,item.png,512,count)
            else:
                im = ItemImage(item.name,item.price,priceIcon,item.rarity,item.priceIconLink,512,count)
            daily.append(im.out())
        if len(shopdata.data.featured) > 4:
            size = 5
        else:
            size = 4
        out = ShopImage(size=300, padding=40, fontsize=40, rowsize=size, fcount=len(shopdata.data.featured), dcount=len(shopdata.data.daily), date=date, background=None)
        overlay = yield from out.generate(featured,daily,fname)
    if len(backgrounds) == 1:
        background = backgrounds[0]
    elif len(backgrounds) > 0:
        background = choice(backgrounds)
    else:
        background = None
    if background == None:
        output = overlay
        output.save(fname)
        newname = fname
    else:
        background_generator = images.Background((overlay.width,overlay.height),url=background)
        output = yield from background_generator.generate()
        output.paste(overlay,(0,0),overlay)
        newname = '{0}-{1}.png'.format(fname[:-4],serverid)
        output.save(newname)
        if not isfile(fname):
            overlay.save(fname)
    return newname
def getShopData(apikey):
    print("Getting shop data")
    shopdata = fnbr.ShopAndSeen(apikey).send()
    return shopdata
def getTime(isotime):
    return datetime.strptime(isotime, "%Y-%m-%dT%H:%M:%S.%fZ")
def filename(time):
    return "{0}.png".format(time.strftime("%Y%m%d%H%M"))
