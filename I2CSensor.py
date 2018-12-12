import time
import smbus
import random
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
    def __init__(self, address, bus=None, on_data=None):
        self.i2c_address = address
        self.on_data = on_data
        self.total_ttr = 0

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
    # end of __init__

    def __on_data__(self, ddict):
        # if there is a callback function, we will
        # call it without printing anything. if there
        # is not a callback specified, we will print
        # what we read.
        if self.on_data != None:
            self.on_data(ddict)
        else:
            print(ddict)
        # end if
    # end __on_data__()

    #removed definitions of kevin to celsius & kevin to f

    def add_ttr(self, ts1, ts2):
        # add ttr method adds the time to do
        # a reading of an object. ts1 and ts2 are
        # both timestamp objects. ts1 is always the
        # earlier timestamp
        ttr = ts2 - ts1

        # this line adds the ttr to the class
        # ttr tracker
        self.total_ttr = self.total_ttr + ttr
    # end add_ttr

    def reset_total_ttr(self):
        # reset total ttr method, this will
        # reset the class variable
        self.total_ttr = 0
    # end of reset_total_ttr

    def read_address(self, address):
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

        # adds the time to read to the class
        # variable
        self.add_ttr(ts1, ts2)

        # sleep for the given period. if the data is read faster
        # than this, it will probably error
        time.sleep(self.read_interval)

        # return the raw data value
        return raw
    # end read_address

    def convert_temp(self, kelvin_value, decimal_places=None):
        # this method converts a kelvin
        # temperature to celcius and fahrenheit
        # and returns it in a dictionary. If decimal_places
        # is specified, it will round the value to that amount
        # of decimal places.

        # celsius calculation
        if decimal_places != None:
            c = round(kelvin_value - 273.15, 2)
            f = round((c * 1.8) + 32, 2)
        else:
            c = kelvin_value - 273.15
            f = (c * 1.8) + 32
        # end if

        tdict = {
            'kelvin':kelvin_value,
            'celcius':c,
            'fahrenheit': f
        }

        return tdict
    # end kelvin_to_celsius

    def read_ambient(self, decimal_places):
        # reads the raw value
        raw_value = self.read_address(self.ambient_address)

        # converts the ambient to the wated units and
        # returns it in a dictionary
        return self.convert_temp(raw_value, decimal_places)
    # end read_ambient

    def read_object(self, decimal_places):
        # gets the raw value for the object
        raw_value = self.read_address(self.object_address)

        # real value is the converted value based on the
        # data sheet for the data at that address
        real_value = raw_value * 0.02

        # converts the ambient to the wated units and
        # returns it in a dictionary
        return self.convert_temp(real_value, decimal_places)
    # end read_object

    def read_emissivity(self, decimal_places=None):
        # gets the raw value for the object
        raw_value = self.read_address(self.emissivity_address)

        # real value is the converted value based on the
        # data sheet for the data at that address
        if decimal_places != None:
            real_value = round(raw_value / 65535, 2)
        else:
            real_value = raw_value / 65535
        # end if

        return real_value
    # end of read_emissivity

    def loop_forever(self, sample_rate=0.25):
        """
            this method is a blocking method. This
            should be called on the last night of the
            main program because any code after will
            not get executed. If a non-blocking function
            is needed, a new thread will have to be
            generated. Usually, I will start by inheriting
            the thread class and daemonize it.
        """
        
        # initialize total ttr
        self.reset_total_ttr()
        
        while True:    

            # initialize the data dictionary
            ddict = {}

            # take the readings
            ddict['object'] = self.read_object(2)
            ddict['emissivity'] = self.read_emissivity(2)

            self.__on_data__(ddict)
        # end while
    # end loop_forever

    def take_readings(self, reading_count, sample_rate=0.25):

        # reinitialize total_ttr in case this methos
        # gets called more than once
        self.reset_total_ttr()

        for i in range(0, reading_count):

            # initialize the data dictionary
            ddict = {}

            # take the readings
            ddict['object'] = self.read_object(2)
            ddict['emissivity'] = self.read_emissivity(2)

            self.__on_data__(ddict)
        # end for
    # end take_readings

    def get_total_ttr(self, reset=False):

        # this method simply returns the
        # running total. if the reset parameter
        # is specified, it will reset the total
        # ttr class variable.
            
        # buffer the total ttr so we
        # can return it
        ttr = self.total_ttr

        # if reset is specified, then call
        # the reset method
        if reset:
            self.reset_total_ttr()
        # end if

        # returns the class variable
        return ttr
    # returns the total_ttr
# end of i2c sensor_count class