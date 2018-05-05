from datetime import datetime

def isotime(string):
    return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
def epoch_now():
    return datetime.utcnow().timestamp()
