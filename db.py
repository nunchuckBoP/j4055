# -----------------------------------------------------------
# the purpose of this class is to 
# connect to a remote mysql database and insert
# records to it.
# -----------------------------------------------------------
import mysql.connector
import model
import threading
import time
import json
from datetime import datetime

class Interface(object):

    def __init__(self, config_file):
        super(Interface, self).__init__()

        self.config_file = config_file
        self.cursor = None
        self.connection = None
        self.data_queue = []
        self.running = False
        self.broken_connection = False
        self.thread = threading.Thread(target=self.run)
        self.new_thread_needed = False

        # connection status to the server
        self.__connected__ = False

    # end of __init__()

    def __connect__(self):

        # load the config file data
        with open(self.config_file) as handle:
            config = json.loads(handle.read())
        # end with

        try:
            print("connecting to database...")
            print("database configuration: %s" % config)
            self.connection = mysql.connector.connect(**config)
            self.cursor = self.connection.cursor()
            self.__connected__ = True
        except Exception as ex:
            print("DATABASE CONNECTION ERROR: %s" % ex)
            self.__connected__ = False
    # end connect

    def __disconnect__(self):
        self.connection.close()
        self.cursor = None

        self.__connected__ = False
        
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
            
            #print("record processed.")
            return ret
        
        except Exception as ex:
            print("Command: %s SQL ERROR: %s" % (command_string, ex))
            return None
        # end try
    # end execute sql command

    def __get_reading_id__(self, from_db=True):
        if from_db or self.reading_index == -1:
            sql_command = "SELECT id from tbl_reading ORDER BY id desc LIMIT 1"
            data = self.__execute_sql_command__(sql_command, None, True)
            #print("__get_reading_id__ = %s" % data)
            if data is not None and data.__len__() > 0:
                return int(data[0][0]) + 1
            else:
                return 0
            # end if
        else:
            self.reading_index = self.reading_index + 1
    # end get reading_id

    def __insert_series__(self, aSeries):
        sql_command_string = ("INSERT INTO tbl_series (id) VALUES(%s)" % aSeries.get_id())
        
        self.__execute_sql_command__(sql_command_string, None, False)
    # end __insert_series__()

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

    def add_data(self, data_object):
        # data object can be: Series, Reading, Temperature, Emissivity, 
        # this is the method to add a reading into the
        # data queue and start logging into the database
        self.data_queue.append(data_object)
        if not self.running:
            # if a new thread is needed, then we
            # will recreate it.
            if self.new_thread_needed:
                self.thread = threading.Thread(target=self.run)
            # end if

            # start the thread
            self.thread.start()
        # end if
    # end add_data

    def kill(self):
        #print("db thread flagged for death.")
        self.running = False
    # end of kill()

    def run(self):
        self.running = True

        #print("started db logging thread..")

        # if we have to connect more than three times,
        # we will have to give up.
        connection_attempts = 0
        
        while self.running:
            
            #if self.__connected__ == False and self.broken_connection == False:
            #    # connect to the database
            #    self.__connect__()
            # end if
            while (self.__connected__ == False and self.running):
                if self.running:
                    self.__connect__()
                # end
                if not self.__connected__:
                    print("MYSQL SERVER CONNECTION ERROR, THREAD WAITING 20 SECONDS")
                    time.sleep(20)
                # end if
            # end while

            # this will not execute unless the server
            # gets connected
            #print("db connected = %s" % self.__connected__)

            if self.data_queue.__len__() > 0:

                # gets the first data object in the queue
                data_object = self.data_queue[0]
                
                # process the reading
            
                # determine the type of data object
                # can either be a series or reading

                if type(data_object) is model.Series:

                    # inserts the series data into the database. If we get an error
                    # we need to break the thread.
                    _inserted = self.__insert_series__(data_object)
                    
                    if _inserted is None:

                        # set the kill it
                        self.running = False
                        
                    # end if

                elif type(data_object) is model.Reading:
                    # first, get the id of the reading. This should
                    # be the last database index in the table. So, for
                    # this we need to query the db for the latest index
                    # value.
                    _reading_id = self.__get_reading_id__(True)
                    data_object.set_id(_reading_id)

                    # insert the reading into the reading table
                    self.__insert_reading__(data_object)
                
                    if type(data_object.get_data()) is type(model.Temperature):
                        
                        # insert temperature into temperature table
                        self.__insert_temperature__(data_object.id, a_reading.get_data())
                    
                    elif type(data_object.get_data()) is type(model.Emissivity):
                        
                        # insert emissivity into emissivity table
                        self.__insert_emissivity__(data_object.id, data_object.get_data())

                    # end if
                else:
                    print("ERROR: Unsupported data type %s" % type(data_object))
                # end if

                # pop the record off of the queue
                self.data_queue.pop(0)
            else:
                # this is there are no more records
                # in the data queue
                self.running = False
            # end if
        # end while loop
        
        # if there is no more data to log, disconnect from the server
        if self.__connected__:
            self.__disconnect__()
        # end if

        self.new_thread_needed = True
    # end of run
# end of class

##if __name__ == '__main__':
##
##    import sensitive_info
##
##    mysql_host = sensitive_info.MYSQL_HOST
##    mysql_database = sensitive_info.MYSQL_DATABASE
##    mysql_username = sensitive_info.MYSQL_USERNAME
##    mysql_password = sensitive_info.MYSQL_PASSWORD
##
##    interface = Interface(mysql_host, mysql_database, mysql_username, mysql_password)
##
##    # timestamp
##    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
##
##    device_address = 0x67
##    ambient_address = 0x24
##    emissivity_address = 0x25
##    object_address = 0x21
##
##    # this is a test main that will seed the database
##    reading1 = model.Reading("ambient", device_address, ambient_address, 0.002, 273.03, ts, model.Temperature(273.03))
##
##    # add the reading to the database
##    interface.add_reading(reading1)
##
##    reading2 = model.Reading("emissivity", device_address, emissivity_address, 0.002, 1.00, ts, model.Emissivity(1.00))
##    interface.add_reading(reading2)
##    
##    for i in range(0, 99):
##        # this is a test main that will seed the database
##        reading = model.Reading("object", device_address, object_address, 0.0001, 273.03, ts, model.Temperature(273.03))
##        interface.add_reading(reading)
##    # end for
##
##    # lets perform a while loop just to be sure the 
##    # mysql grunt work is on a different thread.
##    for i in range(0, 100):
##        print("sleeping %s of 100" % i)
##        time.sleep(0.5)
##    # end for
##
##    print("done.")
### end main
