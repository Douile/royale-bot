from .core import HTTPResponseData

def handle(path,headers,data):
    lowerpath = path.lower()
    if path.startswith('/api/webhooks/heroku'):
        response = HTTPResponseData(200,'application/json','{"wip":"wip"}')
    else:
        response = HTTPResponseData(404,'application/json','')
    return response
