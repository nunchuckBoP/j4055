# main.py modified for counting/timing purposes to main_count.py using I2CSensor_count.py
# CREATION DATE: 11/28/2018
# PROGRAM AUTHOR: CJ (CJ@NEECHSOFT.COM)
# CPU: RASPBERRY PI 3
# PROGRAM DESCRIPTION:
#       THE PROGRAM TAKES READINGS FROM AN IR TEMPERATURE SENSOR
#       USING A CUSTOM CLASS CALLED SENSOR INSIDE THE I2CSensor
#       PYTHON FILE.
#
#       PROGRAM VARIABLES BELOW: SAMPLE_RATE - time the program will
#                               wait between readings
#                               DEVICE_ADDRESS - ADDRESS OF I2C DEVICE (hex)
#                                                                                          READING_COUNT - NUMBER OF READINGS THE PROGRAM
#                               WILL TAKE
#
#       on_data:                This is a callback function for the Sensor
#                               class. The input variable is a dictionary
#                               with the data inside. If there is no callback
#                               supplied it will print the data inside of the
#                               class method. The user can take the data outside
#                               of the callback method for futher processing
#
#       device data registers:  The program reads data register 0x07 (full word)
#       0x07                    Which takes in bytes at address 0x07 and 0x08
#
#       loop_forever:           This class method does the same as the take_readings
#                               method, but the reading_count is infinite
#
#
# TO RUN THE FILE:              python3 main.py or in Rpi Pixel open programming,
#                               click on Programming>>python (2 or 3) and select
#                               Recent Files or search folders. Rerun file: F5
#
#
#       to add line numbers:    Add extension IDLEX, see: idlex.sourceforge.net
#
#       to format print:        see: https//www.python-course.eu/python3_formatted_output.php
#
#
# import the class file. This file needs to be in the
# same directory as this main_count.py file
import I2CSensor



# program variables adjustable
# sample rate in seconds
SAMPLE_RATE = 0.00001

# device address on i2c bus
DEVICE_ADDRESS = 0x5a

#Known addresses in MLX90614 sensor memory are:
#observed object temperature data address is 0x07

#Ambient temperature data address is 0x06
#Ambient temperature data can be process same as observed object temperature

#Emissivity value (1.0 or less, use format %$1.3F) address is 0x04
#Emissivity data can be read the same way but needs to be processed as a float.
#the read temperature command is written on line 74 of I2CSensor module

# number of readings you want
# to take
READING_COUNT = 100

# on_data - callback method for the class
# the output can be used for further processing
# here.
def on_data(ddict):
    # prints out the data
    # dictionary from the sensor.

    # seeing how we don't want to print everything
    # that comes out of the class, we will initialize a
    # new variable called print_data. We map in the values
    # that we want to print out.
    print_data = {
            'kelvin':ddict['kelvin'],
            'celsius':ddict['celsius'],
            'fahrenheit':ddict['fahrenheit'],
            'emissivity':ddict['emissivity'],
            'ambient':ddict['ambient']
        }
    
    # print the data
    print(print_data)

# end on_data

if __name__ == '__main__':

    # instantiates the I2CSensor class. When the data is read
    # from the sensor, the on_data method will be called.
    sensor = I2CSensor.Sensor(address=DEVICE_ADDRESS, sim_mode=False, on_data=on_data)

    # loop forever - blocking call
    # use this method if you want constant readings.
    # the input to the method is a sample rate in
    # seconds.
    # ---COMMENT THIS OUT IF YOU WANT A SET NUMBER OF
    # READINGS.---
    #sensor.loop_forever(SAMPLE_RATE)

    # discrete method for a set number of readings
    # at a given sample rate
    # ---COMMENT THIS OUT IF YOU WANT TO CONTINUOUSLY

    
    # READ DATA.---
    sensor.take_readings(reading_count=READING_COUNT, sample_rate=SAMPLE_RATE)

    #comment out the above line and uncomment the one below
    #if you just want the total time printed

    print(" Total ttr %s" % round(sensor.get_total_ttr(), 4))
