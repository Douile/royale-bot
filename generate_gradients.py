import asyncio
import PIL.Image
import PIL.ImageDraw
from utils import images
from os.path import join
from os import getcwd

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
def main(loop, size):
    dir = getcwd()
    yield from fortnite_uncommon(size, join(dir, 'assets/fortnite_uncommon.png'))
    yield from fortnite_rare(size, join(dir, 'assets/fortnite_rare.png'))
    yield from fortnite_epic(size, join(dir, 'assets/fortnite_epic.png'))
    yield from fortnite_legendary(size, join(dir, 'assets/fortnite_legendary.png'))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    size = (512, 512)
    loop.run_until_complete(main(loop, size))
