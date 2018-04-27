from postgres import Postgres

class Table:
    def __init__(self,name,if_not_exists=False):
        self.name = name
        self.if_not_exists = if_not_exists
        self.columns = []
    def add_column(self, name, type='int', unique=False, not_null=False, primary_key=False):
        self.columns.append(Column(name,type,unique,not_null,primary_key))
    def __str__(self):
        str = "CREATE TABLE %s" % self.name
        if self.if_not_exists:
            str += " IF NOT EXISTS"
        if len(self.columns) > 0:
            str += " ("
            for column in self.columns:
                str += str(column) + ","
            str += ")"
        return str

class Column:
    def __init__(self, name, type='int', unique=False, not_null=False, primary_key=False):
        self.name = name
        self.type = type
        self.unique = unique
        self.not_null = not_null
        self.primary_key = primary_key
    def __str__(self):
        str = "%s %s" % (self.name, self.type)
        if self.unique:
            str += " UNIQUE"
        if self.not_null:
            str += " NOT NULL"
        if self.primary_key:
            str += " PRIMARY KEY"
        return str

class ServerData(Table):
    def __init__(self):
        super().__init__("server_data",True)
        self.add_column("_id",primary_key=True)
        self.add_column("server_id",type="text",unique=True,not_null=True)
        self.add_column("server_name",type="text")
        self.add_column("last_help_msg",type="text")
        self.add_column("last_help_channel",type="text")
        self.add_column("next_shop",type="int")
        self.add_column("latest_shop",type="text")
        self.add_column("prefix",type="text")
class ServerBackgrounds(Table):
    def __init__(self):
        super().__init__("server_backgrounds",True)
        self.add_column("_id",primary_key=True)
        self.add_column("server_id",type="text",not_null=True)
        self.add_column("background_url",type="text")
class ServerChannels(Table):
    def __init__(self):
        super().__init__("server_channels",True)
        self.add_column("_id",primary_key=True)
        self.add_column("server_id",type="text",not_null=True)
        self.add_column("channel_type",type="text",not_null=True)
        self.add_column("channel_id",type="text")
class Cache(Table):
    def __init__(self):
        super().__init__("cache_data",True)
        self.add_column("_id",primary_key=True)
        self.add_column("type",type="text",not_null=True)
        self.add_column("value",type="text")

class Database(Postgres):
    def __init__(self,*,url):
        super().__init__(url)
        self.setupDefaults()
    def setup_defaults(self):
        self.run(str(ServerData))
        self.run(str(ServerBackgrounds))
        self.run(str(ServerChannels))
        self.run(str(Cache))

    # server info
    def servers(self):
        info = self.all("SELECT server_id FROM server_info",back_as=dict,default=None)
        server_ids = []
        if info != None:
            for server in info:
                if 'server_id' in server:
                    server_ids.append(server['server_id'])
    def server_info(self,serverid,backgrounds=False,channels=False):
        info = self.one("SELECT * FROM server_data WHERE server_id=%(id)s",
            parameters={'id': serverid},
            back_as=dict,
            default=None)
        if backgrounds:
            backgrounds_data = self.all("SELECT * FROM server_backgrounds WHERE server_id=%(id)s",
            parameters={'id':serverid},
            back_as=dict,
            default=None)
            info['backgrounds'] = []
            for background in backgrounds_data:
                info['backgrounds'].append(background['background_url'])
        else:
            info['backgrounds'] = None
        if channels:
            channels_data = self.all("SELECT * FROM server_channels WHERE server_id=%(id)s",
            parameters={'id':serverid},
            back_as=dict,
            default=None)
            info['channels'] = {}
            for channel in channels_data:
                info['channels'][channel['channel_type']] = channel['channel_id']
        else:
            info['channels'] = None
        return info
    def set_server_info(self,server_id,server_name=None,last_help_msg=None,last_help_channel=None,next_shop=None,latest_shop=None,prefix=None):
        if not self.is_server(server_id):
            self.run("INSERT INTO server_info (server_id) VALUES (%(id)s)",parameters={'id':server_id})
        if server_name != None:
            self.set_server_info_string(server_id,'server_name',server_name)
        if last_help_msg != None:
            self.set_server_info_string(server_id,'last_help_msg',last_help_msg)
        if last_help_channel != None:
            self.set_server_info_string(server_id,'last_help_channel',last_help_channel)
        if next_shop != None:
            self.set_server_info_int(server_id,'next_shop',next_shop)
        if latest_shop != None:
            self.set_server_info_string(server_id,'latest_shop',latest_shop)
        if prefix != None:
            self.set_server_info_string(server_id,'prefix',prefix)
    def set_server_info_string(self,server_id,column,value):
        self.set_server_info_raw(server_id,column,value,"s")
    def set_server_info_int(self,server_id,column,value):
        self.set_server_info_raw(server_id,column,value,"i")
    def set_server_info_raw(self,server_id,column,value,type="s"):
        self.run("UPDATE server_info %(column)s=%(value){} WHERE server_id=%(id)s".format(type),parameters={'id':server_id,'column':column,'value':value})
    def is_server(self,server_id):
        data = self.one("SELECT _id FROM server_info WHERE server_id=%(id)s",parameters={'id':server_id},default=None)
        exists = False
        if data == None:
            exists = False
        else:
            exists = True
        return exists

    # server backgrounds
    def add_server_background(self,server_id,background_url=None):
        self.run("INSERT INTO server_backgrounds (server_id,background_url) VALUES (%(id)s,%(url)s)",parameters={'id':server_id,'url':background_url})
    def reset_server_backgrounds(self,server_id):
        self.run("DELETE FROM server_backgrounds WHERE server_id=%(id)s",parameters={'id':server_id})
    def set_server_backgrounds(self,server_id,backgrounds=[]):
        self.reset_server_backgrounds(server_info)
        for background in backgrounds:
            self.add_server_background(sever_id,background)

    # server channels
    def set_server_channel(self,server_id,channel_type,channel_id=None):
        if channel_id == None:
            if is_server_channel(server_id,channel_type):
                self.run("DELETE FROM server_channels WHERE server_id=%(id)s AND channel_type=%(type)s",parameters={'id':server_id,'channel_type':channel_type})
        else:
            if is_server_channel(server_id,channel_type):
                self.run("UPDATE server_channels channel_id=%(channel)s WHERE server_id=%(id)s AND channel_type=%(type)s",parameters={'id':server_id,'channel':channel_id,'type':channel_type})
            else:
                self.run("INSERT INTO server_channels (server_id,channel_type,channel_id) VALUES (%(id)s,%(type)s,%(channel)s)",parameters={'id':server_id,'type':channel_type,'channel':channel_id})
    def is_server_channel(self,server_id,channel_type):
        data = self.one("SELECT _id FROM server_channels WHERE server_id=%(id)s AND channel_type=%(type)s",parameters={'id':server_id,'type':channel_type},default=None)
        exists = False
        if data == None:
            exists = False
        else:
            exists = True
        return exists

    # cache data
    def get_cache(self,type,once=False):
        info = self.all("SELECT value FROM cache_data WHERE type=%(type)s",parameters={'type':type},default=None,back_as=dict)
        if once:
            cache = {}
            if info != None:
                for data in info:
                    cache[data['type']] = data['value']
        else:
            cache = []
            if info != None:
                for data in info:
                    cache.append(data['value'])
        return cache
    def set_cache(self,type,value,once=False):
        params = {'value':value,'type':type}
        if once:
            if self.is_cache(type):
                self.run("UPDATE cache_data value=%(value)s WHERE cache_type=%(type)s",parameters=params)
            else:
                self.run("INSERT INTO cache_data (type,value) VALUES (%(type)s,%(value)s)",parameters=params)
        else:
            self.run("INSERT INTO cache_data (type,value) VALUES (%(type)s,%(value)s)",parameters=params)
    def is_cache(self,type):
        info = self.one("SELECT _id FROM cache_data WHERE type=%(type)s",parameters=params)
