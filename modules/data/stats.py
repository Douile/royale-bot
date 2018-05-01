from . import trackernetwork

def getStats(key,name,platform):
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
