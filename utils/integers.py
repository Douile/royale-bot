def min(value,min):
    if value < min:
        value = min
    return value
def max(value,max):
    if value > max:
        value = max
    return value
def bounds(value,min,max):
    if value < min:
        value = min
    elif value > max:
        value = max
    return value
def highest(*args):
    value = None
    for a in args:
        if value == None:
            value = a
        elif a > value:
            value = a
    return value
def lowest(*args):
    value = None
    for a in args:
        if value == None:
            value = a
        elif a < value:
            value = a
