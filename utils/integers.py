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
def highest(value_a,value_b):
    if value_a > value_b:
        value = value_a
    elif value_b > value_a:
        value = value_b
    else:
        value = value_a
    return value
