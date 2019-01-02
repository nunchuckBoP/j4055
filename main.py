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
import i2c_sensor
import mysql_config
import db
import time

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
def on_data(data_reading):
    # this is the callback for the on_data method
    # of the class object. The method takes in a 
    # model.reading class object.
    print(data_reading)
# end on_data

if __name__ == '__main__':

    # create the class that will interact with the database
    db_interface = db.Interface(mysql_config.MYSQL_HOST, mysql_config.MYSQL_DATABASE,
                                mysql_config.MYSQL_USERNAME, mysql_config.MYSQL_PASSWORD)

    # instantiates the I2CSensor class. When the data is read
    # from the sensor, the on_data method will be called.
    sensor = i2c_sensor.Sensor(address=DEVICE_ADDRESS, bus=None,
                               on_data=on_data, db_interface=db_interface)

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
    print("----------------------------------------------------")
    print(" Starting to read data...")
    print("----------------------------------------------------")
    sensor.take_readings(reading_count=READING_COUNT, sample_rate=SAMPLE_RATE)

    #comment out the above line and uncomment the one below
    #if you just want the total time printed

    print("----------------------------------------------------")
    print(" Total ttr %s" % round(sensor.get_total_ttr(), 4))
    print("----------------------------------------------------")
    print(" Max TTR %s" % sensor.get_max_ttr().ttr)
    #print(" Max TTR READING %s" % sensor.get_max_ttr())
    print("----------------------------------------------------")
    print(" Max Object Temperature: %s C" % sensor.get_max_object_temp().get_data().get_celcius())
    #print(" Max Object Temperature READING %s" % sensor.get_max_object_temp())
    print("----------------------------------------------------")

    # loop and rest while the database
    # class is processing readings.
    try:
        print("waiting for db thread to complete...")
        buffer_size1 = db_interface.data_queue.__len__()
        print("sql records to be logged: %s" % buffer_size1)
        while db_interface.is_alive():
            #print("db thread running..buffer length=%s" % db_interface.data_queue.__len__())
            buffer_size2 = db_interface.data_queue.__len__()
            if buffer_size2 < buffer_size1:
                print("sql records to be logged: %s" % buffer_size2)
                buffer_size1 = buffer_size2
            # end if                
            time.sleep(0.1)
        # end while
    except KeyboardInterrupt:
        print("terminating db thread...could take up to 2 minutes for sql connection timeout. Output will appear regaurding thread termination.")
        while db_interface.is_alive():
            db_interface.kill()
            time.sleep(0.1)
        # end while
    # end try

    print("main thread complete.")
