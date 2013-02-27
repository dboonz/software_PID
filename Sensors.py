import numpy as np

class Sensor:

    def __init__(self):
        self.signal_size = 10000

        self.signal = np.array([0]*self.signal_size)

    def getMeasurement(self):
        """ update self.signal. Return average value """
        pass

    def close(self):
        print "Closing sensor"

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

class SensorSim(Sensor):
    def __init__(self):
        self.average = 0.0
        self._std = 0.5
        Sensor.__init__(self)
        self.unit = 'V'
    
    def getMeasurement(self):
        self.signal = np.random.rand(self.signal_size)

        self.signal = np.random.normal(self.average, 
                                       self._std,
                                       self.signal_size)

        self.average = 3 + 0.5*np.random.rand()

        self._std = np.random.rand() * 0.05
        return self.average 

    def mean(self):
        """ Return the mean of the last signal"""
        return self.signal.mean()

    def std(self):
        """ Return std for the last signal"""
        return self.signal.std()
    
    def SIM_set_average(self, average):
        self.average = average

    def SIM_set_std(self, std):
        self._std = std

if __name__ == '__main__':
    with SensorSim() as sensor:
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
