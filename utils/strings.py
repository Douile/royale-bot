# string utils
from urllib.parse import quote_plus


def stripAdditionalReturns(string):
    newstring = ''
    lines = string.split("\n")
    for line in lines:
        if len(line.strip()) > 0:
            newstring += line+'\n'
    return newstring
def uriencode(string):
    if type(string) is int:
        string = str(string)
    return quote_plus(bytes(string,"utf-8"))
def strDec(dec):
    string = ''
    if type(dec) is int or type(dec) is float:
        string = str(dec)
    elif type(dec) is str:
        string = dec
    else:
        raise ValueError('You must pass a string, int or float.')
    try:
        i = string.index('.')
        s = len(string)-i+1
        for b in range(1,s):
            a = s-b
            if string[a] == '0':
                string = string[:a]
            else:
                break
    except ValueError:
        pass
    if string.endswith('.'):
        string = string[:-1]
    return string
def startmatches(string, matches):
    search_string = string.lower().strip()
    doesMatch = None
    for match in matches:
        if search_string.startswith(match.lower().strip()):
            doesMatch = match
            break
    return doesMatch

def num_after(string,text):
    i = string.find(text)+len(text)
    b = string[i:]
    s = ''
    for c in range(0,len(b)):
        d = ord(b[c])
        if d > 47 and d < 58:
            s += b[c]
        else:
            if len(s) > 0:
                break
    try:
        v = int(s)
    except ValueError:
        v = None
    return v

def includes(string,*values):
    t = True
    for value in values:
        if string.find(value) < 0:
            t = False
            break
    return t
