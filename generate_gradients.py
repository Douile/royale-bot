import asyncio
import PIL.Image
import PIL.ImageDraw
from utils import images
from os.path import join
from os import getcwd
import sys

@asyncio.coroutine
def generate_gradient(size, gradient):
    """Generate an image with a radial gradient.
    size: tuple
        must be a tuple of two integers containing the size of the image
    gradient: tuple
        must be tuple of two colors
    """
    image = PIL.Image.new('RGBA', size)
    draw = PIL.ImageDraw.Draw(image)
    images.radial_gradient(draw, size[0], size[1], gradient[0], gradient[1])
    return image


@asyncio.coroutine
def save_gradient(size, gradient, filename):
    image = yield from generate_gradient(size, gradient)
    saved = True
    try:
        image.save(filename)
    except IOError:
        saved = False
    return saved


@asyncio.coroutine
def round_image(image): # deprecated: add_corners
    size = 25
    cornertopleft = yield from generate_corner(size,image.getpixel((1,1)))
    cornertopright = yield from generate_corner(size,image.getpixel((image.width-2,1)))
    cornertopright = cornertopright.rotate(270)
    cornerbottomleft = yield from generate_corner(size,image.getpixel((1,image.height-2)))
    cornerbottomleft = cornerbottomleft.rotate(90)
    cornerbottomright = yield from generate_corner(size,image.getpixel((image.width-2,image.height-2)))
    cornerbottomright = cornerbottomright.rotate(180)
    image.paste(cornertopleft,(0,0))
    image.paste(cornertopright,(image.width-size,0))
    image.paste(cornerbottomleft,(0,image.height-size))
    image.paste(cornerbottomright,(image.width-size,image.height-size))
    return image


@asyncio.coroutine
def generate_corner(size,fill): # deprecated: add_corners
    corner = PIL.Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = PIL.ImageDraw.Draw(corner)
    draw.pieslice((0, 0, size * 2, size * 2), 180, 270, fill=fill)
    return corner


@asyncio.coroutine
def add_corners(im):
    rad = 25
    circle = PIL.Image.new('L', (rad * 2, rad * 2), 0)
    draw = PIL.ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = PIL.Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im


@asyncio.coroutine
def fortnite_uncommon(size, filename):
    gradient = ((96, 170, 58, 255), (23, 81, 23, 255))
    saved = yield from save_gradient(size, gradient, filename)
    return saved
@asyncio.coroutine
def fortnite_rare(size, filename):
    gradient = ((73, 172, 242, 255), (20, 57, 119, 255))
    saved = yield from save_gradient(size, gradient, filename)
    return saved
@asyncio.coroutine
def fortnite_epic(size, filename):
    gradient = ((177, 91, 226, 255), (75, 36, 131, 255))
    saved = yield from save_gradient(size, gradient, filename)
    return saved
@asyncio.coroutine
def fortnite_legendary(size, filename):
    gradient = ((211, 120, 65, 255), (120, 55, 29, 255))
    saved = yield from save_gradient(size, gradient, filename)
    return saved

@asyncio.coroutine
def fortnite_gradient(size, rarity, round):
    fname = yield from filename(rarity, round)
    gradient = RARITIES.get(rarity)
    if gradient is not None:
        image = yield from generate_gradient(size, gradient)
        if round:
            image = yield from add_corners(image)
        image.save(fname)
    else:
        raise ValueError('Rarity not found. Please check RARITIES')

RARITIES = {
    'uncommon': ((96, 170, 58, 255), (23, 81, 23, 255)),
    'rare': ((73, 172, 242, 255), (20, 57, 119, 255)),
    'epic': ((177, 91, 226, 255), (75, 36, 131, 255)),
    'legendary': ((211, 120, 65, 255), (120, 55, 29, 255))
}
FILE_BASE = 'assets/fortnite_{rarity}{rounded}.png'

class NameMap(dict):
    def __missing__(self, key):
        return ''
@asyncio.coroutine
def filename(rarity, rounded=False):
    nmap = NameMap()
    nmap['rarity'] = rarity
    if rounded:
        nmap['rounded'] = '_rounded'
    else:
        nmap['rounded'] = ''
    path = FILE_BASE.format_map(nmap)
    dir = getcwd()
    return join(dir, path)

@asyncio.coroutine
def main(size, round):
    for rarity in RARITIES:
        yield from fortnite_gradient(size, rarity, round)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    size = (512, 512)
    if 'round' in sys.argv:
        round = True
    else:
        round = False
    loop.run_until_complete(main(size, round))
