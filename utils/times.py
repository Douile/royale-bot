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

def day_string(timeSecs):
    minutes = floor(timeSecs/60)
    seconds = timeSecs - (minutes)*60
    hours = floor(minutes/60)
    minutes -= hours*60
    days = floor(hours/24)
    hours -= days*24
    string = '{0}d {1}h {2}m {3}s'.format(days,hours,minutes,seconds)
    return string
