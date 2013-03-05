import threading
import Tkinter as Tk
import numpy as np
import time
from Regulators import HighTemperatureException, LowTemperatureException
from ConfigParser import SafeConfigParser
import Queue
import Sensors
import Regulators

sensordict = {
        'NI-USB-DirkSIM' : Sensors.SensorSim
        }

regulatorDict = {
        'Comb_baseplate_chiller':Regulators.T255ControllerSim
        }


class Controller(threading.Thread):
    def __init__(self, configurationfile, section):
        """ Create a regulator thread. Use configurationfile for the
        parser, and read section section of it. One section corresponds to
        one regulator. Relevant parameters are gathered from the
        Sensors.ini and the Regulators.ini file. """
        print "Arguments: "
        print "Configurationfile %s\tsection %s" % (configurationfile, section)
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.configurationfile = configurationfile
        self.configparser = SafeConfigParser()
        self.configparser.read(self.configurationfile)
        self.label = section
        self.initialize()

    def initialize(self):
        """ Load all the relevant variables from the .ini file"""
        get = lambda s:self.configparser.get(self.label,s)
        getfloat  = lambda s:self.configparser.getfloat(self.label,s)
        getint  = lambda s:self.configparser.getint(self.label,s)

        try :

            self.stop = False
            self.feedback = False
            
            # finding the right controller and sensor
            # find out what other sections we'll have to read as well
            sensorkey = get("sensor")
            regulatorkey = get("regulator")
            # look up the corresponding class in the regulator and load it with
            # it's section_name as an argument 
            self.sensor = sensordict[sensorkey](sensorkey)
            self.regulator = regulatorDict[regulatorkey](regulatorkey)

            # log file
            self.logfile = get('logfile') + '-' + self.label + '.dat'

            # queue to put measured values in 
            self.sensor_queue = Queue.Queue(maxsize=20)
            self.regulator_queue = Queue.Queue(maxsize=20)
            self.time_queue = Queue.Queue(maxsize=20)

            # sensor properties
            self.sensor_unit = get('sensor_unit')
            self.sensor_high = getfloat('sensor_high')
            self.sensor_low = getfloat('sensor_low')
            self.sensor_fraction = getfloat('sensor_fraction')
            self.recalculate_range()

            # regulator properties
            self.regulator_max = get('regulator_max')
            self.regulator_min = get('regulator_min')
            self.regulator_unit = get('regulator_unit')
            self.regulator_label = get('regulator_label')

            # regulator properties
            self.time_between_measurements =\
                 getfloat('time_between_measurements')
            # time between runs of the feedback loop
            self.feedback_deadtime = getfloat('feedback_deadtime')
        except ValueError:
            print "Error reading configfile"
            raise

    def recalculate_range(self):
        """ If the parameters of sensor_high and sensor_low have been
        changed, it is important to recalculate the range  in which the
        signal can be. This function does just that """
        high = self.sensor_high
        low  = self.sensor_low
        fraction = self.sensor_fraction
        mean = ( high + low ) / 2. 
        _range = high - low


        self.max_signal = mean + _range * 0.5 * fraction
        self.min_signal = mean - _range * 0.5 * fraction
        # devices for feedback



    def run(self):
        """ Main loop: Perform measurements when the feedback loop is on
        """
        self.lastfeedbacktime = time.time()
        while True:
            while not self.stop:
                print "Taking measurement"
                self.takeMeasurement()
                if self.feedback:
                    print "Performing feedback"
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
        """ Retrieve a measurement. """
        self.last_sensor_value = self.sensor.get_value()
        self.last_regulator_value = self.regulator.get_value()
        self.last_measurement_time = time.time()

        # put the last measured values in a queue. They can be retrieved by
        # the main program to put them in a graph.
        try :
            self.time_queue.put_nowait(self.last_measurement_time)
            print "time queue length: ", self.time_queue.qsize()
            self.sensor_queue.put_nowait(self.last_sensor_value)
            self.regulator_queue.put_nowait(self.last_regulator_value)
        except Queue.Full:
            print "Queue full, not appending anymore"


    def performFeedback(self, debug=True):
        """ Do the feedback. if debug == True, show the values """
        # feedback should be performed every N seconds. So if it has not been
        # elapsed, don't do anything
        if time.time() - self.lastfeedbacktime < self.feedback_deadtime:
            return
        else :
            mean = self.last_sensor_value

            if debug is True:
                print "Mean signal: %3.2f" % mean

            if mean > self.max_signal:
                if debug:
                    print "Performing negative feedback"
                self.regulator.perform_negative_feedback()
            elif mean < self.min_signal:
                if debug:
                    print "Performing positive feedback"
                self.regulator.perform_positive_feedback()
         


class ControllerWidget:
    """ Widget that contains a controller object. Creates all the buttons. """
    def __init__(self, parent, configurationfile, section):
        """ Class that contains a widget for all the properties in the
        controller.
        
        WARNING: Whole widget is added using pack! So don't mix with grid
        layout manager!"""

        # create widget
        self.parent = parent
        self.section = section

        #  create controller
        self.controller = Controller(configurationfile, section)
        self.time_axis = []
        self.regulator_axis = []
        self.sensor_axis = []

        self.createControlButtons()
        print "Created control buttons"

        # start thread 
        self.controller.start()

    def updateData(self):
        """ It is possible to get the data from the feedback loop """
        appenddata = lambda l, s: l.append(s.get_nowait())
        contr = self.controller
        try:
            appenddata(self.time_axis, contr.time_queue)
            appenddata(self.sensor_axis, contr.sensor_queue)
            appenddata(self.regulator_axis, contr.regulator_queue)
        except Queue.Empty:
            pass
   
    def processWidgets(self):
        self.controller.stop = not self.startstopVar.get()
        self.controller.feedback = self.feedbackVar.get()

        # process all text fields
        sc = self.controller
        fields = [sc.sensor_high, sc.sensor_low, sc.sensor_fraction]
        for i in range(len(fields)): #  make any incorrect input red
            try:
                float(self.entryfields[i].get())
                self.entryfields[i]['fg']='black'
            except ValueError:
                self.entryfields[i]['fg']='red'
        try : # set all sensor values to their new values
            sc.sensor_high = float(self.sens_high_entry.get())
            sc.sensor_low = float(self.sens_low_entry.get())
            sc.sensor_fraction = float(self.sens_fraction_entry.get())
            sc.recalculate_range()
        except:
            print "One of the entry fields is not correct. Not doing anything"

        try:
            th = float(self.regulator_max_entry.get())
            self.regulator_max_entry['fg']='black'
        except ValueError:
            self.regulator_max_entry['fg'] = 'red'

        try:
            tl = float(self.regulator_min_entry.get())
            self.regulator_min_entry['fg']='black'
        except ValueError:
            self.regulator_min_entry['fg'] = 'red'

        try :
            self.controller.regulator_min = tl
            self.controller.regulator_max = th 
        except UnboundLocalError:
            print "Could not set regulator limits"

    def entryWithLabelAndVar(self, parent, label, row, start_col, width=5, **kwargs):
        """ Create an entry field with a label and a variable. 
        label is text for the label, row is the row, start_col is the start column,

        Makes a variable content that tracks the text in entry.
        
        Returns content, entry 
        """
        label = Tk.Label(parent, text=label).grid(row=row, column=start_col)
#        content = Tk.StringVar()
        content = 0
        entry = Tk.Entry(parent, width=width, **kwargs)
        entry.grid(row=row, column=start_col+1)
        return content, entry



    def createControlButtons(self):

#        """ Create all the widgets that are needed to control the device"""
        self.frame = Tk.LabelFrame(self.parent, text=self.section)
        self.frame.pack(side=Tk.BOTTOM, fill=Tk.BOTH, expand=1)

#
#        # startstopbutton
        self.startstopVar = Tk.BooleanVar()
        self.startstopcheckbox = Tk.Checkbutton(self.frame,text="Run",
                variable=self.startstopVar)
        self.startstopcheckbox.grid(row=0)
#
#        # feedbackbutton
        self.feedbackVar = Tk.BooleanVar()
        self.feedbackbutton = Tk.Checkbutton(self.frame, 
                                  text="Feedback active", 
                                  variable=self.feedbackVar)
        self.feedbackbutton.grid(row=0, column=1)
#
        self.entryfields = []
        self.sens_high_string, self.sens_high_entry = self.entryWithLabelAndVar(self.frame, "Sensor high ", 1, 0)

#
        self.sens_low_string, self.sens_low_entry = self.entryWithLabelAndVar(self.frame, "Sensor low ", 1, 2)

        self.sens_fraction_string, self.sens_fraction_entry = self.entryWithLabelAndVar(self.frame, "Sensor fraction ", 1, 4)

        self.sens_high_entry.insert(0,self.controller.sensor_high)
        self.sens_low_entry.insert(0,self.controller.sensor_low)
        self.sens_fraction_entry.insert(0,self.controller.sensor_fraction)

        self.entryfields.append(self.sens_high_entry)
        self.entryfields.append(self.sens_low_entry)
        self.entryfields.append(self.sens_fraction_entry)
        # Controller high, low 
#
        self.regulator_max_string, self.regulator_max_entry = self.entryWithLabelAndVar(self.frame, "Regulator max ", 2, 0)
        
        self.regulator_min_string, self.regulator_min_entry = self.entryWithLabelAndVar(self.frame, "Regulator min ", 2, 2)
        
#        # start with default values
        self.regulator_min_entry.insert(0,self.controller.regulator_min)
        self.regulator_max_entry.insert(0,self.controller.regulator_max)

        self.entryfields.append(self.regulator_min_entry)
        self.entryfields.append(self.regulator_max_entry)

        
if __name__ == '__main__':
#     regulator = Controller("settings.ini", "Baseplate")
#     regulator.start()
#     time.sleep(10)
#     print "Closing down"
# 
      root = Tk.Tk()
      root.wm_title("bla")
      bla = ControllerWidget(root,'settings.ini','Baseplate')
      
#      bla2 = ControllerWidget(root, 'settings.ini', 'Baseplate')
      print "Starting tk mainloop"
      Tk.mainloop()
