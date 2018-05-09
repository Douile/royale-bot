class HTTPResponseData:
    def __init__(self,code=500,type='text/html',data=''):
        self.code = code
        self.type = type
        self.response = data
