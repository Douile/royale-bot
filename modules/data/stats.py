from . import trackernetwork

def getStats(key,name,platform):
    response = trackernetwork.StatsRequest(key,name,platform).send()
    stats = {}
    if response.data.lifetimestats != None:
        stats['kdr'] = response.data.lifetimestats.stat('kdr')
        stats['kills'] = response.data.lifetimestats.stat('kills')
        stats['wins'] = response.data.lifetimestats.stat('wins')
        stats['win%'] = response.data.lifetimestats.stat('winpercent')
        stats['games'] = response.data.lifetimestats.stat("matchesplayed")
    else:
        print(response.status)
        print(response.headers)
    data = {'name':response.data.epicUserHandle, 'platform': response.data.platformNameLong, 'stats':stats}
    return data
