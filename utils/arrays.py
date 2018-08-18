def split(arr, size):
     arrs = []
     while len(arr) > size:
         pice = arr[:size]
         arrs.append(pice)
         arr   = arr[size:]
     arrs.append(arr)
     return arrs

def message_string(*items,split='or'):
    item_list = []
    for item in items:
        if type(item) is list:
            item_list += item
        elif type(item) is str or type(item) is int or type(item) is float:
            item_list.append(str(item))
        elif type(item) is dict:
            for key in item:
                item_list.append('{0}: {1}'.format(key,item.get(key,'')))
    item_string = ''
    for i in range(0,len(item_list)):
        if i < 1:
            item_string += '`{0}`'.format(item_list[i])
        elif i > len(item_list)-2:
            item_string += ' {0} `{1}`'.format(split,item_list[i])
        else:
            item_string += ', `{0}`'.format(item_list[i])
    return item_string

class Array(list):
    def search(self,test):
        ind = -1
        if callable(test):
            for v in self:
                if test(v):
                    ind = self.index(v)
                    break
        else:
            for v in self:
                if getattr(v,'id',None) == test:
                    ind = self.index(v)
                    break
        return ind
    def filter(self,test):
        out = []
        if callable(test):
            for v in self:
                if test(v):
                    out.append(v)
        else:
            for v in self:
                if getattr(v,'id',None) == test:
                    out.append(v)
