import numpy as np
import time
import ConfigParser 

class Sensor:
    """ Sensor for the software_PID. Set up by an .ini file. 
    
    To create a new device, override these methods and put in __ini__:
     def __init__(self, section_name):
        '''Create the simulator'''
        self.section_name = section_name
        Sensor.__init__(self)

    """
    def __init__(self):
        self.signal = np.array([- 99e99 ])
        self.initialize()

    def initialize(self):
        """ Initialize the device """
        pass


    def getMeasurement(self):
        """ update self.signal. Return average value """
        pass

    def close(self):
        """ To be called whenever the application closes, for instance to clear a device """
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

class SensorSim(Sensor):
    def __init__(self, section_name):
        """ Create the simulator """
        self.section_name = section_name
        Sensor.__init__(self)

        
    def initialize(self):
        """ Read in all the relevant options from Sensors.ini"""
        self.t0 = time.time()

        self.configparser = ConfigParser.SafeConfigParser()
        self.configparser.read("Sensors.ini")

        # read in all variables
        get = lambda s:self.configparser.get(self.section_name,s)
        getfloat = lambda s:self.configparser.getfloat(self.section_name, s)

        self.clockspeed = getfloat("clockspeed")
        self.signal_size = getfloat("signal_size")
        self.port = getfloat("port")

        self.average = getfloat("average")
        self.std = getfloat("std")
    
    def getMeasurement(self):
        """ Make a pseudo-measurement and return the answer. Takes some time."""
        self.signal = np.random.normal(self.average, 
                                       self.std,
                                       self.signal_size) +\
        np.linspace(0,1,self.signal_size)*np.sin((self.t0 - time.time())/2.)
        time.sleep(0.5)
        return self.average 

    def mean(self):
        """ Return the mean of the last signal"""
        return self.signal.mean()

    def std(self):
        """ Return std for the last signal"""
        return self.signal.std()
    
    def SIM_set_average(self, average):
        """ Set average for simulator"""
        self.average = average

    def SIM_set_std(self, std):
        """ Set std for simulator"""
        self.std = std

if __name__ == '__main__':
    with SensorSim("NI-USB-DirkSIM") as sensor:
        print "Press a to set average\npress s to set std\npress m to take\
 a measurement,\npress x to stop"
        stop = False
        while stop is False:
            try :
                print "std mean:" , sensor.signal.std(), sensor.signal.mean()
                command = raw_input()
                if command is 'a':
                    try :
                        average = raw_input("Enter a new value for a")
                        sensor.SIM_set_average(float(average))
                    except: 
                        pass

                elif command is 's':
                    try:
                        std = raw_input("Enter a new value for std")
                        sensor.SIM_set_std(float(std))
                    except:
                        pass

                elif command is 'x':
                    exit(0)
                elif command is 'm':
                    sensor.getMeasurement()
            except:
               raise
