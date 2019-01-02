# -----------------------------------------------------------
# the purpose of this class is to 
# connect to a remote mysql database and insert
# records to it.
# -----------------------------------------------------------
import mysql.connector
import model
import threading
import time
import pickle
from datetime import datetime

class Interface(threading.Thread):

    def __init__(self, server_ip, database, username, password):
        super(Interface, self).__init__()

        self.server_ip = server_ip
        self.database = database
        self.username = username
        self.password = password
        self.cursor = None
        self.connection = None
        self.data_queue = []
        self.running = False

        # connection status to the server
        self.__connected__ = False

        # try and unpickle the reading index

        # if it can't be unpickled then we set it
        # to the default value of -1
        try:
            self.reading_index = pickle.loads("reading_index")
        except Exception as ex:
            self.reading_index = -1
            print("could not unpickle reading_index variable exception: %s" % ex)
        # end try

    # end of __init__()

    def __connect__(self):

        config = {
                'user':self.username,
                'password':self.password,
                'host':self.server_ip,
                'database':self.database
            }

        self.connection = mysql.connector.connect(**config)
        self.cursor = self.connection.cursor()
        self.__connected__ = True
    # end connect

    def __disconnect__(self):
        self.connection.close()
        self.cursor = None

        self.__connected__ = False

        # pickle the reading index. That way
        # we don't have to get it from the
        # server every time.
        if self.reading_index != -1:
            print("pickling reading_index...")
            pickle.dumps(self.reading_index)
        # end if
    # end disconnect

    def __execute_sql_command__(self, command_string, params=None, select=False):
        try:
            if params is not None:
                affected = self.cursor.execute(command_string, params)
                if select:
                    return self.cursor.fetchall()
                else:
                    self.connection.commit()
                    return affected
            else:
                affected = self.cursor.execute(command_string)
                if select:
                    return self.cursor.fetchall()
                else:
                    self.connection.commit()
                    return affected
            # end if
            
            print("record processed.")
            return ret
        
        except Exception as ex:
            print("Command: %s SQL ERROR: %s" % (command_string, ex))
            return None
        # end try
    # end execute sql command

    def __get_reading_id__(self, from_db=True):
        if from_db or self.reading_index == -1:
            sql_command = "SELECT id from ifmt.tbl_reading ORDER BY id desc LIMIT 1"
            data = self.__execute_sql_command__(sql_command, None, True)
            if data is not None and data.__len__() > 0:
                return int(data[0][0]) + 1
            else:
                return 0
            # end if
        else:
            self.reading_index = self.reading_index + 1
    # end get reading_id

    def __insert_reading__(self, aReading):

        # inserts the reading
        sql_command_string = (
                              "INSERT INTO tbl_reading (id, name, series_id, ttr, location_id, device_address, data_address) " 
                              "VALUES(%s, %s, %s, %s, %s, %s, %s)"
                              )
        sql_command_parameters = (aReading.id, aReading.name, aReading.series_id, aReading.ttr, aReading.location_id, aReading.device_address, aReading.data_address)
        self.__execute_sql_command__(sql_command_string, sql_command_parameters, False)

        # if the reading is a temperature value, we insert it into the 
        # temperature table. If the reading is emissivity, then we insert
        # it into that table.
        if type(aReading.get_data()) is model.Temperature:
            self.__insert_temperature__(aReading.id, aReading.get_data())
        elif type(aReading.get_data()) is model.Emissivity:
            self.__insert_emissivity__(aReading.id, aReading.get_data())
        # end if
    # end insert_record

    def __insert_temperature__(self, reading_id, aTemperature):
        sql_command_string = (
                              "INSERT INTO tbl_temperature (reading_id, kelvin, celcius, fahrenheit) "
                              "VALUES(%s, %s, %s, %s)"
                             )
        sql_command_parameters = (reading_id, aTemperature.get_kelvin(), aTemperature.get_celcius(), aTemperature.get_fahrenheit())
        self.__execute_sql_command__(sql_command_string, sql_command_parameters, False)
    # end insert_temperature

    def __insert_emissivity__(self, reading_id, aEmissivity):
        sql_command_string = (
                              "INSERT INTO tbl_emissivity (reading_id, value) "
                              "VALUES(%s, %s)"
                              )
        sql_command_parameters = (reading_id, aEmissivity.get_value())
        self.__execute_sql_command__(sql_command_string, sql_command_parameters, False)
    # end insert_emissivity

    def add_reading(self, a_reading):
        # this is the method to add a reading into the
        # data queue and start logging into the database
        self.data_queue.append(a_reading)
        if not self.running:
            self.start()
        # end if
    # end add_reading

    def run(self):
        self.running = True

        while self.running:

            if self.__connected__ == False:
                self.__connect__()
            # end if

            # gets the first reading in the queue
            a_reading = self.data_queue[0]
            
            # process the reading
            # insert reading into reading table
            if a_reading.has_id() == False:
                a_reading.set_id(self.__get_reading_id__(True))
            # end if

            # insert the reading into the reading table
            self.__insert_reading__(a_reading)

            if type(a_reading.get_data()) is type(model.Temperature):
                
                # insert temperature into temperature table
                self.__insert_temperature__(a_reading.id, a_reading.get_data())
            
            elif type(a_reading.get_data()) is type(model.Emissivity):
            
                # insert emissivity into emissivity table
                self.__insert_emissivity__(a_reading.id, a_reading.get_data())
            
            # end if

            # pop the record off of the queue
            self.data_queue.pop(0)

            # check the length of the queue - if it is empty,
            # stop running
            if self.data_queue.__len__() == 0:
                self.running = False
            # end if
        # end while loop

        # if there is no more data to log, disconnect from the server
        self.__disconnect__()

        print("data queue empty.")

    # end of run
# end of class

if __name__ == '__main__':

    import sensitive_info

    mysql_host = sensitive_info.MYSQL_HOST
    mysql_database = sensitive_info.MYSQL_DATABASE
    mysql_username = sensitive_info.MYSQL_USERNAME
    mysql_password = sensitive_info.MYSQL_PASSWORD

    interface = Interface(mysql_host, mysql_database, mysql_username, mysql_password)

    # timestamp
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    device_address = 0x67
    ambient_address = 0x24
    emissivity_address = 0x25
    object_address = 0x21

    # this is a test main that will seed the database
    reading1 = model.Reading("ambient", device_address, ambient_address, 0.002, 273.03, ts, model.Temperature(273.03))

    # add the reading to the database
    interface.add_reading(reading1)

    reading2 = model.Reading("emissivity", device_address, emissivity_address, 0.002, 1.00, ts, model.Emissivity(1.00))
    interface.add_reading(reading2)
    
    for i in range(0, 99):
        # this is a test main that will seed the database
        reading = model.Reading("object", device_address, object_address, 0.0001, 273.03, ts, model.Temperature(273.03))
        interface.add_reading(reading)
    # end for

    # lets perform a while loop just to be sure the 
    # mysql grunt work is on a different thread.
    for i in range(0, 100):
        print("sleeping %s of 100" % i)
        time.sleep(0.5)
    # end for

    print("done.")
# end main
