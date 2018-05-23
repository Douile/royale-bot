from utils import getEnv
from utils.times import tommorow, now
from datetime import datetime
from instagram_private_api import Client
from PIL import Image
from imagegeneration import shop
import asyncio
import traceback

INSTAGRAM_USER = getEnv('INSTAGRAM_USER')
INSTAGRAM_PASS = getEnv('INSTAGRAM_PASS')
KEY_FNBR = getEnv("KEY_FNBR")
if INSTAGRAM_PASS == None or INSTAGRAM_USER == None or KEY_FNBR == None:
    raise RuntimeError('Please supply enviroment variables')
BACKGROUNDS = []



def readPhoto(name):
    with open(name,'rb') as file:
        content = file.read()
    return content

def post_photo(photo, caption):
    api = Client(INSTAGRAM_USER, INSTAGRAM_PASS)
    photo_data = Image.open(photo)
    photo_data.save('temp_insta.jpg')
    bytes_photo = readPhoto('temp_insta.jpg')
    size_photo = photo_data.size
    r = api.post_photo(bytes_photo, size_photo, caption=caption)
    print(r)
    api.logout()

def caption():
    text = '#fortnite shop for {}'
    date = datetime.utcnow().strftime('%d %B')
    text.format(date)
    return text

@asyncio.coroutine
def main():
    while 1:
        next_time = tommorow() - now() + 60*5
        yield from asyncio.sleep(next_time)
        shopdata = shop.getShopData(KEY_FNBR)
        image = yield from shop.generate(shopdata, BACKGROUNDS, 'instagram')
        try:
            post_photo(image, caption())
        except:
            traceback.print_exc()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
