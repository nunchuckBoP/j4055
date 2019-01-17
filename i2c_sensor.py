import time
import smbus
import random
import model
class Sensor(object):
    """
        I2CSensor - general class for an I2CSensor
        Author: CJ (cj@neechsoft.com)
        Date: 11/28/2018
        Job #: j4055 (Infrared temperature sensor)
        Constructor:
            address - hex address of the i2c sensor
            on_data - callback function when the data from the
                      sensor is read

        Methods:
            loop_forever - loops forever continuously reading the data
                           it also monitors the time it takes to read.
    """
    def __init__(self, address, bus=None,
                 on_data=None, db_interface=None):
        
        # i2c bus address of device
        self.i2c_address = address

        # on data callback function
        self.on_data = on_data
        
        # series id - this is used for the
        # database.
        self.series = None

        # total time to read class variable
        self.total_ttr = 0

        # maximum time to read time class
        # variable. this is a dictionary
        # containing the information on the max
        # ttr reading
        self.max_ttr = 0
        self.max_ttr_reading = None

        # maximum object temperature class
        # variables. The decimal variable is in
        # kelvin.
        self.max_object_temp = 0
        self.max_object_temp_reading = None

        # hard-coded data registers for the 
        # type of sensor. This should be consistent
        # if there is more than one sensor on the
        # bus
        self.ambient_address = 0x6
        self.object_address = 0x7
        self.emissivity_address = 0x24

        # I found this in the documentation
        # so we will put this in just to be
        # safe.
        self.read_interval = 1.44 / 1000
         
        # initialize the bus. We will do that
        # once in the initialize function. Hopefully
        # doing this only once will speed up the
        # device read times.
        if bus is None:
            self.bus = smbus.SMBus(1)
        else:
            self.bus = bus
        # end if

        # this is the database interface class
        # if an instance is detected then we will
        # send the data on a reading.
        self.db_interface = db_interface

    # end of __init__

    def add_ttr(self, ttr):
        self.total_ttr = self.total_ttr + ttr
    # end of add_ttr

    def get_total_ttr(self):

        # this method simply returns the
        # running total. if the reset parameter
        # is specified, it will reset the total
        # ttr class variable.
            
        # buffer the total ttr so we
        # can return it
        ttr = self.total_ttr

        # returns the class variable
        return ttr
    # returns the total_ttr

    def reset_total_ttr(self):
        # reset total ttr method, this will
        # reset the class variable
        self.total_ttr = 0
    # end of reset_total_ttr

    def get_max_ttr(self):
        return self.max_ttr_reading
    # end get_max_ttr()

    def get_max_object_temp(self):
        return self.max_object_temp_reading
    # end of get_max_object_temp

    def __on_data__(self, aReading):
        # if there is a callback function, we will
        # call it without printing anything. if there
        # is not a callback specified, we will print
        # what we read.
        if self.on_data != None:
            self.on_data(aReading)
        else:
            print(aReading)
        # end if

        # if the database is not none, then
        # there should be a good path to the
        # db, and we will add it for logging
        if self.db_interface is not None:
            self.db_interface.add_data(aReading)
        # end if
    # end __on_data__()

    #removed definitions of kevin to celsius & kevin to f

    def read_device(self, address, name=None, conversion=1.0,
                    data_type="temperature"):
        # this method will do the grunt
        # reading of the address and
        # return back the raw value. It also
        # will keep track of the total_ttr
        
        # first timestamp
        ts1 = time.time()

        # raw reading from the device
        raw = self.bus.read_word_data(self.i2c_address, address)

        # timestamp 2
        ts2 = time.time()

        # gets the time to read
        ttr = ts2 - ts1

        # adds the ttr to the total ttr
        self.add_ttr(ttr)

        # instatiates the reading object
        reading = model.Reading(name, self.i2c_address, address,
                                ttr, raw, self.series.get_id())

        # sets the data on the reading
        if data_type == "temperature":
            reading.set_data(model.Temperature(raw * conversion))
        elif data_type == "emissivity":
            reading.set_data(model.Emissivity(raw * conversion))
        else:
            print("ERROR: UNSUPPORTED DATA TYPE IN READ_DEVICE METHOD")
        # end if

        # keeps track of the max time to read value
        # and data object that it occured at.
        if ttr > self.max_ttr:
            self.max_ttr = ttr
            self.max_ttr_reading = reading
        # end if

        # sleep for the given period. if the data is read faster
        # than this, it will probably error
        time.sleep(self.read_interval)

        # return the raw data value
        return reading
    # end read_address

    def take_readings(self, reading_count=None, sample_rate=0.25):

        # this is where we need to set the series id
        self.series = model.Series(time.time())

        # add the series object in the data queue
        self.db_interface.add_data(self.series)

        # reinitialize total_ttr in case this methos
        # gets called more than once
        self.reset_total_ttr()

        # take the ambient reading first.
        ambient_reading = self.read_device(self.ambient_address, "ambient", 0.02, "temperature")

        # we call the on_data event to let the main
        # program access the reported data.
        self.__on_data__(ambient_reading)
        
        # take the emissivity reading
        emissivity_reading = self.read_device(self.emissivity_address, "emissivity", (1/65535), "emissivity")

        # fire the on_data event so the main routine
        # can print the data
        self.__on_data__(emissivity_reading)

        # volitile boolean that will break the loop
        # if set to false.
        looping = True

        # index local variable to keep track of how
        # many iterations took place. If it gets to the read count
        # then it will break the loop.
        _index = 0
        while looping:

            # take the readings
            object_reading = self.read_device(self.object_address, "object", 0.02, "temperature")

            # keep track of the maximum object reading
            if object_reading.get_data().get_kelvin() > self.max_object_temp:
                self.max_object_temp = object_reading.get_data().get_kelvin()
                self.max_object_temp_reading = object_reading
            # end if

            # this calls the on_data callback event
            self.__on_data__(object_reading)

            # time to sleep. Since we build in a defualt time
            # between readings based off of the datasheet. We
            # will subtract this time from the sample rate. Because
            # we already slept that long on the last reading
            sleep_time = sample_rate - self.read_interval
            if sleep_time > 0:
                time.sleep(sleep_time)
            # end if

            # this code breaks out of the loop if a reading
            # count is specified.
            if reading_count is not None:
                if _index == reading_count - 1:
                    looping = False
                else:
                    _index = _index + 1
                # end if
            # end if
        # end for
    # end take_readings
# end of i2c sensor_count class
