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
    def __init__(self, address, sim_mode=False, on_data=None):
         self.address = address
         self.on_data = on_data
         self.sim_mode = sim_mode
         self.total_ttr = 0
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

    def read(self):
        
        # get the current timestamp
        ts1 = time.time()
        
        # return dictionary
        ddict = {}

        # initialize the bus
        bus = smbus.SMBus(1)

        # reads the data from the bus
        raw = bus.read_word_data(self.address, 0x07)
        
        # sleep for a fraction of a second
        time.sleep(0.01)
        
        # read the next address
        raw2 = bus.read_word_data(self.address, 0x04)
        
        # emissivity correction coefficient
        # the raw value comes in as 70-75 so is
        # it raw / 100?
        emissivity = raw2 * 0.01

        # read the time after reading data
        ts2 = time.time()

        #calculation of temperatures from data read
        kelvin = round(raw * 0.02, 2)
        celsius = round((kelvin - 273.15), 2)
        fahrenheit = round((celsius * 1.8) + 32, 2)
        
        ddict['kelvin'] = kelvin       
        ddict['celsius'] = celsius
        ddict['fahrenheit'] = fahrenheit
        ddict['emissivity'] = emissivity

        # calculate the elapse time to read to this point
        ttr = ts2 - ts1
        
        # ttr is the time to read the data (removed from ddict printout)
        ddict["ttr"] = ttr

        # this keeps the running ttr total
        self.total_ttr = self.total_ttr + ttr
        
        # call the function
        self.__on_data__(ddict)

    # end read()

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
        while True:
            self.read()
            time.sleep(sample_rate)
        # end while
    # end loop_forever

    def take_readings(self, reading_count, sample_rate=0.25):

        # reinitialize total_ttr in case this methos
        # gets called more than once
        self.total_ttr = 0
        
        for i in range(0, reading_count):
            self.read()
            time.sleep(sample_rate)
        # end for
    # end take_readings

    # this method simply returns the
    # running total
    def get_total_ttr(self):
        return self.total_ttr
    # returns the total_ttr
# end of i2c sensor_count class




