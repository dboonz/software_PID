import threading
import time
from Regulators import HighTemperatureException, LowTemperatureException

class Regulator(threading.Thread):
    def __init__(self, configurationfile, name):
        threading.Thread.__init__(self)
        self.configurationfile = configurationfile
        self.name = name
        self.initialize()
        self.setDaemon(True)

    def initialize(self):
        """ Load all the relevant variables from the .ini file"""
        self.stop = True
        self.feedback = True

        # sensor properties
        self.sensorport = 0
        self.sensor_high = 5
        self.sensor_low = 3

        # feedback properties
        self.time_between_measurements = 3 #  time between two measurements
        self.feedback_deadtime = 1 #  time between two runs of the
        # feedback loop
        self.max_signal = 2
        self.min_signal = 0

        # devices for feedback
        from Regulators import T255ControllerSim
        from Sensors import SensorSim
        self.regulator = T255ControllerSim()
        self.sensor = SensorSim()

    def run(self):
        """ Main loop: Perform measurements when the feedback loop is on
        """
        self.lastfeedbacktime = time.time()
        self.stop = False
        while True:
            
            while self.stop is False:
                print "Taking measurement"
                self.takeMeasurement()
                print "performing feedback"
                self.performFeedback()
                time.sleep(self.time_between_measurements)

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
                print "Mean signal: %3.2f", mean
                print "std signal : %3.2f", std
            
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
    regulator = Regulator("bla", "bla")
    regulator.start()
    time.sleep(30)

