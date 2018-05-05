from datetime import datetime

def isotime(string):
    if string.endswith('Z'):
        time = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        time = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%f")
    return time
def epoch_now():
    return datetime.utcnow().timestamp()
