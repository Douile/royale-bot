def min(value,min):
    if value < min:
        value = min
    return value
def bounds(value,min,max):
    if value < min:
        value = min
    elif value > max:
        value = max
    return value
