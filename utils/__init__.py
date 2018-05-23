from . import strings, arrays, integers, images

def getEnv(name,default=None):
    value = os.environ.get(name,None)
    if value == None:
        if default == None:
            value = input("Env variable not found, please enter {}: ".format(name))
        else:
            value = default
    return value
