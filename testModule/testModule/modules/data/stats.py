from . import trackernetwork

def getStats(key,name,platform):
    response = trackernetwork.StatsRequest(key,name,platform).send()
    stats = {}
    stats['kdr'] = response.data.lifetimestats.kdr
    stats['kills'] = response.data.lifetimestats.kills
    stats['wins'] = response.data.lifetimestats.wins
    stats['win%'] = response.data.lifetimestats.winpercent
    stats['games'] = response.data.lifetimestats.matchesplayed
    data = {'name':response.data.epicUserHandle, 'platform': response.data.platformNameLong, 'stats':stats}
    return data
