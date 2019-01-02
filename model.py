class Reading(object):
    def __init__(self, name, device_address, data_address, ttr, raw_value, series_id, data=None, location_id=0):
        
        # this data could be useful down the line
        # when there may be multiple devices attached
        # to the database
        self.name = name
        self.device_address = device_address
        self.data_address = data_address
        self.raw_value = raw_value
        self.series_id = series_id
        self.id = None
        self.location_id = location_id

        # reading the data items
        self.ttr = ttr
        self.data = None
        if data is not None:
            self.data = data
        # end if
    # end __init__()

    def has_id(self):
        if self.id is None:
            return False
        else:
            return True
        # end if
    # end has_id

    def set_id(self, id):
        self.id = id
    # end set_id

    def set_data(self, data):
        # this method overrites whatever
        # is in the data
        self.data = data
    # end set_data
    
    def get_data(self):
        # returns the data object. This should
        # be either a temperature or emissivity 
        # reading.
        return self.data
    # end get_data

    def __str__(self):
        # this is the method that gets called when it is "printed"
        _string = "name: %s    device address: %s    data address: %s    data: %s" % \
            (self.name, self.device_address, self.data_address, self.get_data().__str__())
        return _string
# end reading

class Temperature(object):
    def __init__(self, kelvin):
        self.kelvin = kelvin
        self.table_name = "tbl_temperature"
    # end init

    def get_kelvin(self, decimal_places=None):
        if decimal_places is None:
            return self.kelvin
        else:
            return round(self.kelvin, decimal_places)
        # end if
    # end get_kelvin

    def get_celcius(self, decimal_places=None):
        val = self.kelvin - 273.15
        if decimal_places is None:
            return val
        else:
            return round(val, decimal_places)
        # end if
    # end get_celcius

    def get_fahrenheit(self, decimal_places=None):
        c = self.kelvin - 273.15
        val = (c * (9/5) ) + 32
        if decimal_places is None:
            return val
        else:
            return round(val, decimal_places)
        # end if
    # end get_fahrenheit

    def __str__(self):
        # this is the method that gets called when it is "printed"
        _string = "kelvin: %s    celcius: %s    fahrenheit: %s" % \
            (self.get_kelvin(2), self.get_celcius(2), self.get_fahrenheit(2))
        return _string
# end temperature

class Emissivity(object):

    def __init__(self, value):
        self.value = value
    # end __init__

    def get_value(self, decimal_places=None):
        if decimal_places is None:
            return self.value
        else:
            return round(self.value, decimal_places)
        # end if
    # end get_value

    def __str__(self):
        # this is the method that gets called when it is "printed"
        return "emissivity: %s" % self.get_value(2)
    # end __str__()

# end emissivity