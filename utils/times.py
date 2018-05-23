from datetime import datetime
from time import mktime

def isotime(string):
    if string.endswith('Z'):
        time = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        time = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%f")
    return time
def epoch_now():
    return datetime.utcnow().timestamp()

def now():
    t = datetime.utcnow()
    return mktime(t.utctimetuple())

def morning():
    tnow = now()
    morning = tnow - (now.hour*60*60) - (now.minute*60) - (now.second)
    return morning

def tommorow():
    m = morning()
    return m + 60*60*24
