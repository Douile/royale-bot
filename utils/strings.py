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
        s = len(string)-i
        for b in range(1,s):
            a = len(string)-b
            if string[a] == '0':
                string = string[:a]
                if a >= s-1:
                    string = string[:i]
            else:
                break
    except ValueError:
        pass
    return string
