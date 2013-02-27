import threading
import time
from Regulators import HighTemperatureException, LowTemperatureException
from ConfigParser import SafeConfigParser
import Queue

class Controller(threading.Thread):
    def __init__(self, configurationfile, section):
        """ Create a regulator thread. Use configurationfile for the
        parser, and read section section of it. One section corresponds to
        one regulator. Relevant parameters are gathered from the
        Sensors.ini and the Regulators.ini file. """
        threading.Thread.__init__(self)
        self.configurationfile = configurationfile
        self.configparser = SafeConfigParser()
        self.configparser.read(self.configurationfile)
        self.label = section
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

            # find out what other sections we'll have to read as well
            sensortype = getstring("sensor_type")
            regulatortype = getstring("regulator_type")

            self.configparser.read("Regulators.ini")
            self.configparser.read("Sensors.ini")

            # log file
            self.logfile = getstring('logfile') + '-' + self.label + '.dat'

            # queue to put measured values in 
            self.sensor_queue = Queue.Queue(maxsize=20)
            self.regulator_queue = Queue.Queue(maxsize=20)
            self.time_queue = Queue.Queue(maxsize=20)

            # sensor props from Sensors.ini
            self.sensor_unit = self.configparser.get(sensortype,"sensor_unit")
            self.sensor_label = self.configparser.get(
                                sensortype,"sensor_label")

            # sensor properties
            self.sensorport = getint('sensor_port')
            self.sensor_high = getfloat('sensor_high')
            self.sensor_fraction = getfloat('sensor_fraction')
            self.sensor_low = getfloat('sensor_low')

            self.recalculate_range()

            # regulator properties
            self.time_between_measurements =\
                 getfloat('time_between_measurements')
            # time between runs of the feedback loop
            self.feedback_deadtime = getfloat('feedback_deadtime')
            from Regulators import T255ControllerSim
            from Sensors import SensorSim

            self.regulator = T255ControllerSim()
            self.sensor = SensorSim()
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
        last_sensor_value = self.sensor.getMeasurement()

        last_regulator_value = self.regulator.get_value()
        last_measurement_time = time.time()

        # put the last measured values in a queue. They can be retrieved by
        # the main program to put them in a graph.
        try :
            self.time_queue.put_nowait(last_measurement_time)
            self.sensor_queue.put_nowait(last_sensor_value)
            self.regulator_queue.put_nowait(last_regulator_value)
        except Queue.Full:
            print "Queue full, not appending anymore"


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

import Tkinter as Tk

class ControllerWidget:
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

        # create callbacks

        # start thread
        self.controller.start()

    def updateData(self):
        """ It is possible to get the data from the feedback loop """
        appenddata = lambda l, s: l.append(s.get_nowait())
        contr = self.controller
        try:
            appenddata(self.time_axis,contr.time_queue)
            appenddata(self.sensor_axis, contr.sensor_queue)
            appenddata(self.regulator_axis, contr.regulator_queue)
        except Queue.Empty:
            pass
   
    def processWidgets(self):
        # startstopbutton
        
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
            pass



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
            self.controller.regulator.set_limits(tl,th)
        except UnboundLocalError:
            print "Could not set temperature limits"



    def createControlButtons(self):
        """ Create all the widgets that are needed to control the device"""
        self.frame = Tk.LabelFrame(self.parent, text=self.section)
        self.frame.pack(side=Tk.BOTTOM, fill=Tk.BOTH, expand=1)

        # startstopbutton
        self.startstopVar = Tk.BooleanVar()
        self.startstopcheckbox = Tk.Checkbutton(self.frame,text="Run",
                variable=self.startstopVar)
        self.startstopcheckbox.grid(row=0)

        # feedbackbutton
        self.feedbackVar = Tk.BooleanVar()
        self.feedbackbutton = Tk.Checkbutton(self.frame, 
                                  text="Feedback active", 
                                  variable=self.feedbackVar)
        self.feedbackbutton.grid(row=0, column=1)

        self.entryfields = []
        # Sensor high and low, and range
        Tk.Label(self.frame, text="Sensor high [%s]" %
                self.controller.sensor.unit).grid(row=1,column=0)
        self.sens_high_entry = Tk.Entry(self.frame, width=5)
        self.sens_high_entry.grid(row=1, column=1)


        Tk.Label(self.frame, text="Sensor low [%s]" %
                self.controller.sensor.unit).grid(row=1,column=2)
        self.sens_low_entry = Tk.Entry(self.frame, width=5)
        self.sens_low_entry.grid(row=1, column=3)

        Tk.Label(self.frame, text="Sensor fraction [0-1]").grid(row=1,
                column=4)
        self.sens_fraction_entry = Tk.Entry(self.frame, width=5)
        self.sens_fraction_entry.grid(row=1, column=5)

        self.sens_high_entry.insert(0,self.controller.sensor_high)
        self.sens_low_entry.insert(0,self.controller.sensor_low)
        self.sens_fraction_entry.insert(0,self.controller.sensor_fraction)

        self.entryfields.append(self.sens_high_entry)
        self.entryfields.append(self.sens_low_entry)
        self.entryfields.append(self.sens_fraction_entry)
        # Controller high, low 

        Tk.Label(self.frame, text="Regulator Max [%s]" %
                self.controller.regulator.unit).grid(row=2, column=0)
        self.regulator_max_entry = Tk.Entry(self.frame, width=5)
        self.regulator_max_entry.grid(row=2, column=1)
        
        
        Tk.Label(self.frame, text="Regulator Min [%s]" %
                self.controller.regulator.unit).grid(row=2, column=2,
                        sticky='W')
        self.regulator_min_entry = Tk.Entry(self.frame, width=5)
        self.regulator_min_entry.grid(row=2, column=3, columnspan=2,
                sticky='W')
        
        # start with default values
        self.regulator_min_entry.insert(0,self.controller.regulator.min_temperature)
        self.regulator_max_entry.insert(0,self.controller.regulator.max_temperature)

        self.entryfields.append(self.regulator_min_entry)
        self.entryfields.append(self.regulator_max_entry)

        # keep track of the last 100 measurements to plot in a circular
        # buffer




        

if __name__ == '__main__':
#     regulator = Controller("settings.ini", "Baseplate")
#     regulator.start()
#     time.sleep(30)
# 
      root = Tk.Tk()
      root.wm_title("bla")
      bla = ControllerWidget(root,'settings.ini','Baseplate')
      bla2 = ControllerWidget(root, 'settings.ini', 'Baseplate')
      Tk.mainloop()
