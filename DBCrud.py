# -----------------------------------------------------------
# the purpose of this class is to 
# connect to a remote mysql database and insert
# records to it.
# -----------------------------------------------------------

class DBCrudClient:

    def __init__(self, server_ip, username, password):

        self.server_ip = server_ip
        self.username = username
        self.password = password
    # end of __init__()

    def connect(self):
        pass
    # end connect

    def disconnect(self):
        pass
    # end disconnect

    def insert_record(self, record_dict):
        pass
    # end insert_record
# end of class.
