# string utils

def stripAdditionalReturns(string):
    newstring = ''
    lines = string.split("\n")
    for line in lines:
        if len(line.strip()) > 0:
            newstring += line+'\n'
    return newstring
