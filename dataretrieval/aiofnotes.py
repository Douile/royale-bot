import asyncio
import aiohttp
import bs4
import html2text

from utils import strings

PATCHNOTES = 'https://www.epicgames.com/fortnite/api/blog/getPosts?category=patch+notes&postsPerPage={0}&offset={1}&locale=en-US'


@asyncio.coroutine
def fetch_patch_notes(limit=5,offset=0,detail=True):
    url = PATCHNOTES.format(limit, offset)
    session = aiohttp.ClientSession()
    response = yield from session.get(url)
    output = {'success': False}
    if response.status == 200:
        data = yield from response.json()
        if 'blogList' in data:
            output['notes'] = []
            for blog in data['blogList']:
                url = 'https://www.epicgames.com/fortnite/en-US{0}'.format(blog.get('externalLink','/'))
                content_response = yield from session.get(url)
                if content_response.status == 200:
                    content = yield from content_response.text()
                else:
                    content = ''
                note = {
                  'title': blog['title'],
                  'author': blog['author'],
                  'image': blog['shareImage'],
                  'date': blog['date'],
                  'short': html2text.html2text(blog['short']),
                  'slug': blog['slug'],
                  'url': url,
                  'detailed': None,
                  'simple': None
                }
                html = bs4.BeautifulSoup(content, 'html.parser')
                if detail == True:
                    try:
                        note['detailed'] = yield from parse_detail_patchnotes(html)
                    except:
                        note['detailed'] = [{'title': 'Parse error', 'value': 'Epic screwed with the api again'}]
                elif detail == False:
                    try:
                        note['simple'] = yield from parse_simple_patchnotes(html)
                    except:
                        note['simple'] = {'description': 'Parse error', 'extra': [], 'video': None}
                output['notes'].append(note)
            output['success'] = True
    else:
        print(response.status_code)
    yield from session.close()
    return output


@asyncio.coroutine
def parse_detail_patchnotes(html):
    contents = []
    outer = html.find('div', attrs={'class': 'patch-notes-view'})
    inner = outer.findChild('div')
    identifier = inner.findChild('h2')
    title = None
    value = ''
    content = identifier.fetchNextSiblings()
    for node in content:
        if node.name == 'ul':
            i = content.index(node)
            content = content[:i] + node.findAll('li', recursive=False) + content[i:]
    for node in content:
        if node.name == 'h2':
            if title != None and value != '':
                contents.append({'title': title, 'value': value})
            if node.name != 'Save the World':
                title = node.getText(strip=True)
            else:
                title = None
            value = ''
        elif node.name == 'li':
            mkdn = yield from markdown(str(node))
            newstr = '- {0}\n'.format(mkdn, baseurl="https://www.epicgames.com").lstrip("* ").strip()
            if len(value)+len(newstr) > 1024:
                contents.append({'title': title, 'value': value})
                value = newstr
                title += ' (continued)'
            else:
                value += newstr
        elif node.name == 'strong':
            newstr = '**{0}**\n'.format(node.getText(strip=True))
            if len(value)+len(newstr) > 1024:
                contents.append({'title':title,'value':value})
                value = newstr
                title += ' (continued)'
            else:
                value += newstr
    if title is not None and value != '':
        contents.append({'title': title, 'value': value})
    return contents


@asyncio.coroutine
def parse_simple_patchnotes(html):
    contents = {'description':'','extra':[],'video':None}
    outer = html.find('div', attrs={'class': 'patch-notes-description'})
    inner = outer.findChild('div')
    content = inner.findAll('p',recursive=False)
    for node in content:
        title = node.find('strong')
        if title == None:
            c = yield from markdown(str(node))
            if len(c.strip()) > 0:
                contents['description'] += c+"\n"
        else:
            titletext = title.getText(strip=True)
            identifier = ' (Battle Royale)'
            if titletext.endswith(identifier):
                realtitle = titletext[:titletext.index(identifier)]
                nodetext = '<%s>' % node.name
                value = html2text.html2text(str(node)[len(nodetext)+len(str(title)):-len(nodetext)-1]).strip('*\n ')
                contents['extra'].append({'title':realtitle,'value':value})
    embed = inner.find('div',{'class':'embed-responsive'})
    if embed != None:
        iframe = embed.find('iframe')
        if iframe != None:
            embedurl = iframe.attrs['src']
            contents['video'] = 'https://youtube.com/watch?v={0}'.format(embedurl.split("/")[-1])
            print('Found video:',contents['video'])
    return contents


@asyncio.coroutine
def markdown(html,baseurl=None):
    converter = html2text.HTML2Text()
    converter.ignore_images = True
    if baseurl != None:
        converter.ignore_links = False
        converter.baseurl = baseurl
    mark = converter.handle(html)
    return strings.stripAdditionalReturns(mark)
