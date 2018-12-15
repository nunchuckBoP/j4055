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
    def __init__(self, address, decimal_places=2, bus=None, on_data=None):
        
        # decimal places is for readout
        # of the data. -1 decimal places is leave the 
        # values unrounded.
        self.decimal_places = decimal_places

        # i2c bus address of device
        self.i2c_address = address

        # on data callback function
        self.on_data = on_data

        # total time to read class variable
        self.total_ttr = 0

        # maximum time to read time class
        # variable. this is a dictionary
        # containing the information on the max
        # ttr reading
        self.max_ttr = 0
        self.max_ttr_meta = {}

        # maximum object temperature class
        # variables. The decimal variable is in
        # kelvin.
        self.max_object_temp = 0
        self.max_object_temp_meta = {}

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

    def reset_total_ttr(self):
        # reset total ttr method, this will
        # reset the class variable
        self.total_ttr = 0
    # end of reset_total_ttr

    def get_max_ttr(self):
        return self.max_ttr_meta
    # end get_max_ttr()

    def get_max_object_temp(self):
        return self.max_object_temp_meta
    # end of get_max_object_temp

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

    def convert_temp(self, kelvin_value):
        # this method converts a kelvin
        # temperature to celcius and fahrenheit
        # and returns it in a dictionary. If decimal_places
        # is specified, it will round the value to that amount
        # of decimal places.

        # celsius calculation
        if self.decimal_places != None:
            c = round(kelvin_value - 273.15, self.decimal_places)
            f = round((c * 1.8) + 32, self.decimal_places)
            k = round(kelvin_value, self.decimal_places)
        else:
            c = kelvin_value - 273.15
            f = (c * 1.8) + 32
            k = kelvin_value
        # end if

        tdict = {
            'kelvin':k,
            'celcius':c,
            'fahrenheit': f
        }

        return tdict
    # end kelvin_to_celsius

    def read_address(self, address, name=None):
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

        # updates the total ttr
        self.total_ttr = self.total_ttr + ttr

        # if reading this address is longer
        # than the max - update it to this
        # ttr value
        if ttr > self.max_ttr:
            self.max_ttr = ttr
            self.max_ttr_meta = {'max ttr':self.max_ttr,
                                 'device address':hex(self.i2c_address),
                                 'data address':hex(address),
                                 'name':name}
        # end if

        # sleep for the given period. if the data is read faster
        # than this, it will probably error
        time.sleep(self.read_interval)

        # return the raw data value
        return (raw, ttr)
    # end read_address

    def read_temperature(self, name):
        
        if name == 'object':
            
            # reads the raw data
            (raw_data, ttr) = self.read_address(self.object_address, name)

            # converts the value from the conversion
            # in the datasheet
            real_value = raw_data * 0.02

            # compare the kelvin value to the max
            # temperature. if it is higher, update
            # the max temp class variable
            if real_value > self.max_object_temp:

                # update the class variable
                self.max_object_temp = real_value

                # save the meta data for the reading
                self.max_object_temp_meta = {"object":self.convert_temp(real_value),
                                             "ttr":ttr}
            # end if

            # returns the data object dictionary
            return {"object":self.convert_temp(real_value), "ttr":ttr}

        elif name == 'ambient':
            
            # reads the raw data
            (raw_data, ttr) = self.read_address(self.ambient_address, name)

            # converts the value from the conversion
            # in the datasheet
            real_value = raw_data * 0.02

            # returns the data object dictionary
            return {"ambient":self.convert_temp(real_value), "ttr":ttr}
        else:
            raise Exception("name not defined.")
        # end if
    # end of read_temp

    def read_emissivity(self):
        # gets the raw value for the object
        (raw_value, ttr) = self.read_address(self.emissivity_address, 'emissivity')

        # real value is the converted value based on the
        # data sheet for the data at that address
        if self.decimal_places != None:
            real_value = round(raw_value / 65535, 2)
        else:
            real_value = raw_value / 65535
        # end if

        return {"emissivity":real_value, "ttr":ttr}
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

        # take the ambient reading first.
        ambient_data = self.read_temperature('ambient')

        # we call the on_data event to let the main
        # program access the reported data.
        self.__on_data__(ambient_data)

        # take the emissivity reading
        emissivity_data = self.read_emissivity()

        # fire the on_data event so the main routine
        # can print the data
        self.__on_data__(emissivity_data)

        # begin the infinite loop
        while True:    

            # initialize the data dictionary
            ddict = {}

            # take the readings
            object_data = self.read_temperature("object")
            
            # time to sleep. Since we build in a defualt time
            # between readings based off of the datasheet. We
            # will subtract this time from the sample rate. Because
            # we already slept that long on the last reading            
            sleep_time = sample_rate - self.read_interval
            if sleep_time > 0:
                time.sleep(sleep_time)
            # end if

            self.__on_data__(object_data)
        # end while
    # end loop_forever

    def take_readings(self, reading_count, sample_rate=0.25):

        # reinitialize total_ttr in case this methos
        # gets called more than once
        self.reset_total_ttr()

        # take the ambient reading first.
        ambient_data = self.read_temperature('ambient')

        # we call the on_data event to let the main
        # program access the reported data.
        self.__on_data__(ambient_data)
        
        # take the emissivity reading
        emissivity_data = self.read_emissivity()

        # fire the on_data event so the main routine
        # can print the data
        self.__on_data__(emissivity_data)

        for i in range(0, reading_count):

            # initialize the data dictionary
            ddict = {}

            # take the readings
            object_data = self.read_temperature("object")

            # time to sleep. Since we build in a defualt time
            # between readings based off of the datasheet. We
            # will subtract this time from the sample rate. Because
            # we already slept that long on the last reading
            sleep_time = sample_rate - self.read_interval
            if sleep_time > 0:
                time.sleep(sleep_time)
            # end if

            self.__on_data__(object_data)
        # end for
    # end take_readings

# end of i2c sensor_count class
