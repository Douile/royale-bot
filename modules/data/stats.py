from . import trackernetwork
import asyncio
import aiohttp

@asyncio.coroutine
def fetch(session, url):
    response = yield from session.get(url)
    return response

@asyncio.coroutine
def apiSession(apikey):
    headers = {'TRN-Api-Key':apikey}
    return aiohttp.ClientSession(headers=headers)

@asyncio.coroutine
def stats(key,player='',platform='pc'):
    url = 'https://api.fortnitetracker.com/v1/profile/{0}/{1}'.format(platform,player)
    print(url)
    session = yield from apiSession(key)
    response = yield from fetch(session, url)
    if response.status == 200:
        json = yield from response.json()
        json['status'] = response.status
    else:
        json = {'status':response.status,'error':response.reason}
    yield from session.close()
    return json


def getStats(key,name='',platform=''):
    response = trackernetwork.StatsRequest(key,name,platform).send()
    if response.data != None:
        stats = {}
        stats['kdr'] = response.data.lifetimestats.stat('kdr')
        stats['kills'] = response.data.lifetimestats.stat('kills')
        stats['wins'] = response.data.lifetimestats.stat('wins')
        stats['win%'] = response.data.lifetimestats.stat('winpercent')
        stats['games'] = response.data.lifetimestats.stat("matchesplayed")
        data = {'name':response.data.epicUserHandle, 'platform': response.data.platformNameLong, 'stats':stats}
    else:
        print(response.status)
        print(response.headers)
    data = {'name':response.status,'platform':''}
    return data
