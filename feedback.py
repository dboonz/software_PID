import threading
import time
from Regulators import HighTemperatureException, LowTemperatureException
from ConfigParser import SafeConfigParser

class Regulator(threading.Thread):
    def __init__(self, configurationfile, label):
        threading.Thread.__init__(self)
        self.configurationfile = configurationfile
        self.configparser = SafeConfigParser()
        self.configparser.read(self.configurationfile)
        self.label = label
        self.initialize()
        self.setDaemon(True)

    def initialize(self):
        """ Load all the relevant variables from the .ini file"""

        try :
            self.stop = False
            self.feedback = True

            getstring = lambda s:self.configparser.get(self.label,s)
            getfloat  = lambda s:self.configparser.getfloat(self.label,s)
            getint  = lambda s:self.configparser.getint(self.label,s)
            
            # log file
            self.logfile = getstring('logfile') + '-' + self.label + '.dat'

            # sensor properties
            self.sensorport = getint('sensor_port')
            self.sensor_high = getfloat('sensor_high')
            self.sensor_fraction = getfloat('sensor_fraction')
            self.sensor_low = getfloat('sensor_low')

            # feedback properties
            self.time_between_measurements =\
                 getfloat('time_between_measurements')
            # time between runs of the feedback loop
            self.feedback_deadtime = getfloat('feedback_deadtime')
            high = self.sensor_high
            low  = self.sensor_low
            fraction = self.sensor_fraction
            mean = ( high + low ) / 2. 
            _range = high - low


            self.max_signal = mean + _range * 0.5 * fraction
            self.min_signal = mean - _range * 0.5 * fraction
            # devices for feedback

            from Regulators import T255ControllerSim
            from Sensors import SensorSim

            self.regulator = T255ControllerSim()
            self.sensor = SensorSim()
        except ValueError:
            print "Error reading configfile"
            raise

    def run(self):
        """ Main loop: Perform measurements when the feedback loop is on
        """
        self.lastfeedbacktime = time.time()
        while True:
            
            while not self.stop:
                
                print "Taking measurement"
                self.takeMeasurement()
                print "performing feedback"
                if self.feedback:
                    self.performFeedback()
                time.sleep(self.time_between_measurements - 0.1)

                self.write_log_message()
            time.sleep(0.1)

    def write_log_message(self, message=None):
        """ Write out a logmessage """
        if message is None:
            message = "%.2f\t%s\t%.2f\t%.2f\n" % (self.sensor.mean(), 
                    self.feedback and "Feedback" or "NoFeedback", 
                    self.regulator.get_value(), self.regulator.get_set_value())

        with open(self.logfile,'a') as logfile:
            logfile.write(message)



    def takeMeasurement(self):
        self.sensor.getMeasurement()
    
    def performFeedback(self, debug=True):
        """ Do the feedback. if debug == True, show the values """
        if time.time() - self.lastfeedbacktime < self.feedback_deadtime:
            return
        else :
            mean = self.sensor.mean()
            std = self.sensor.std()

            if debug is True:
                print "Mean signal: %3.2f" % mean
                print "std signal : %3.2f" % std
            
            if mean > self.max_signal:
                if debug:
                    print "Performing negative feedback"
                try :
                    self.regulator.perform_negative_feedback()
                except HighTemperatureException:
                    print "Could not perform feedback, because on a temp limit"
                except LowTemperatureException:
                    print "Lower feedback limit reached"

            elif mean < self.min_signal:
                if debug:
                    print "Performing positive feedback"
                try:
                    self.regulator.perform_positive_feedback()
                except HighTemperatureException:
                    print "Could not perform feedback, because on a temp limit"
                except LowTemperatureException:
                    print "Lower temperature limit reached "


if __name__ == '__main__':
    regulator = Regulator("settings.ini", "Baseplate")
    regulator.start()
    time.sleep(30)

