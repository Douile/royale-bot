from datetime import datetime
from time import mktime
from math import floor

def isotime(string):
    if string.endswith('Z'):
        time = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        time = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%f")
    return time

def now():
    return datetime.utcnow().timestamp()

def morning():
    now = datetime.utcnow()
    return now.timestamp() - 3600*now.hour - 60*now.minute - now.second

def tommorow():
    m = morning()
    return m + 86400

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
