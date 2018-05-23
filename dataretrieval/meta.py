import requests
import bs4
import html2text
from utils import strings

NEWS = 'https://fortnitecontent-website-prod07.ol.epicgames.com/content/api/pages/fortnite-game'
STATUS = 'https://lightswitch-public-service-prod06.ol.epicgames.com/lightswitch/api/service/bulk/status?serviceId=Fortnite'
STATUS_SERVICES = 'https://status.epicgames.com/'
PATCHNOTES = 'https://www.epicgames.com/fortnite/api/blog/getPosts?category=patch+notes&postsPerPage={0}&offset={1}&locale=en-US'

def markdown(html,baseurl=None):
    converter = html2text.HTML2Text()
    converter.ignore_images = True
    if baseurl != None:
        converter.ignore_links = False
        converter.baseurl = baseurl
    mark = converter.handle(html)
    return strings.stripAdditionalReturns(mark)

def getStatus():
    response = requests.get(STATUS)
    data = response.json()[0]
    output = {'online':False,'message':'','services':{}}
    if data['status'] == 'UP':
        output['online'] = True
    else:
        output['online'] = False
    output['message'] = data['message']
    response = requests.get(STATUS_SERVICES)
    html = bs4.BeautifulSoup(response.text,'html.parser')
    componentscont = html.find('div',attrs={'class':'child-components-container'})
    components = componentscont.findAll('div',recursive=False)
    for component in components:
        name = component.find('span',attrs={'class':'name'}).getText(strip=True)
        status = component.find('span',attrs={'class':'component-status'}).getText(strip=True)
        output['services'][name] = status
    return output

def getNews(language='en'):
    response = requests.get(NEWS,headers={'Accept-Language':'en-US'})
    output = {'success':False}
    if response.status_code == 200:
        data = response.json()
        if 'battleroyalenews' in data:
            output['updated'] = data['battleroyalenews']['lastModified']
            output['messages'] = []
            if 'news' in data['battleroyalenews']:
                if 'messages' in data['battleroyalenews']['news']:
                    output['messages'] = data['battleroyalenews']['news']['messages']
        if 'emergencynotice' in data:
            if 'news' in data['emergencynotice']:
                if 'messages' in data['emergencynotice']['news']:
                    output['messages'] += data['emergencynotice']['news']['messages']
        output['success'] = True
    return output

def getPatchNotes(limit=5,offset=0,detail=True):
    url = PATCHNOTES.format(limit,offset)
    response = requests.get(url)
    output = {'success':False}
    if response.status_code == 200:
        data = response.json()
        if 'blogList' in data:
            output['notes'] = []
            for blog in data['blogList']:
                url = 'https://www.epicgames.com/fortnite/en-US/news/{0}'.format(blog['slug'])
                note = {'title':blog['title'],
                'author':blog['author'],
                'image':blog['shareImage'],
                'date':blog['date'],
                'short':html2text.html2text(blog['short']),
                'slug':blog['slug'],
                'url':url,
                'detailed':None,
                'simple':None}
                html = bs4.BeautifulSoup(blog['content'],'html.parser')
                if detail == True:
                    try:
                        note['detailed'] = parseDetailPatchNotes(html)
                    except:
                        note['detailed'] = [{'title':'Parse error','value':'Epic screwed with the api again'}]
                elif detail == False:
                    try:
                        note['simple'] = parseSimplePatchNotes(html)
                    except:
                        note['simple'] = {'description':'Parse error','extra':[],'video':None}
                output['notes'].append(note)
            output['success'] = True
    else:
        print(response.status_code)
    return output

def parseDetailPatchNotes(html):
    contents = []
    outer = html.find('div',attrs={'id':'overview-section'})
    inner = outer.findChild('div')
    identifier = inner.findChild('h2')
    title = None
    value = ''
    content = identifier.fetchNextSiblings()
    for node in content:
        if node.name == 'ul':
            i = content.index(node)
            content = content[:i] + node.findAll('li',recursive=False) + content[i:]
    for node in content:
        if node.name == 'h2':
            if title != None and value != '':
                contents.append({'title':title,'value':value})
            if node.name != 'Save the World':
                title = node.getText(strip=True)
            else:
                title = None
            value = ''
        elif node.name == 'li':
            newstr = '- {0}\n'.format(markdown(str(node),baseurl="https://www.epicgames.com").lstrip("* ").strip())
            if len(value)+len(newstr) > 1024:
                contents.append({'title':title,'value':value})
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
    if title != None and value != '':
        contents.append({'title':title,'value':value})
    return contents

def parseSimplePatchNotes(html):
    contents = {'description':'','extra':[],'video':None}
    outer = html.find('div',attrs={'id':'overview-section'})
    inner = outer.findChild('div')
    content = inner.findAll('p',recursive=False)
    for node in content:
        title = node.find('strong')
        if title == None:
            c = markdown(node.__str__())
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
