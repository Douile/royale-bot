from datetime import datetime
from time import mktime
from math import floor

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
    now_d = datetime.utcnow()
    morning = tnow - (now_d.hour*60*60) - (now_d.minute*60) - (now_d.second)
    return morning

def tommorow():
    m = morning()
    return m + 60*60*24

def minute_string(timeSecs):
    minutes = floor(timeSecs/60)
    seconds = timeSecs - (minutes*60)
    string = '{0}m {1}s'.format(minutes,seconds)
    return string
