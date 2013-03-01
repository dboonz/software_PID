# import statements
import time
from feedback import ControllerWidget
import matplotlib
matplotlib.use('TkAgg')
import Queue
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,\
NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import ConfigParser
import sys
if sys.version_info[0] < 3:
    import Tkinter as Tk
else:
    import tkinter as Tk


class RootWindow:
    def __init__(self):
        self.setupWindow()
        self.setupGraph()
        self.addWidgets()
        self.startMainLoop()

    def setupWindow(self):
        """ Create the window """
        self.root = Tk.Tk()
        self.root.wm_title("Embedding TK")
        Tk.Grid.columnconfigure(self.root,0, weight=1)
        Tk.Grid.rowconfigure(self.root,0, weight=1)

    def setupGraph(self):
        """ Setup the graph"""
        # create frame to put figure in
        self.figureframe = Tk.Frame(self.root)
        self.figureframe.grid(sticky='NESW')
        Tk.Grid.columnconfigure(self.figureframe, 0, weight=1)

        # t0 for graph (time axis is elapsed time since start of program)
        self.t0 = time.time()
        # create figure
        self.figure = Figure(figsize=(5,4), dpi=75)
        self.axes = self.figure.add_subplot(111)
        self.regulator_axis = self.axes.twinx()

        # canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.figureframe)
        self.canvas.get_tk_widget().pack(side=Tk.TOP, expand=True, fill='both')
        self.canvas.show()

        # toolbar
        toolbar = NavigationToolbar2TkAgg(self.canvas, self.figureframe)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=Tk.TOP, expand=True)

    def addWidgets(self):
        """ Add the widget of the feedback loops """
        self.config = ConfigParser.SafeConfigParser()
        self.config.read("./settings.ini")
        self.widgetsFrame = Tk.LabelFrame(self.root, text="Widgets")
        self.widgetsFrame.grid(row=3, sticky='EW')
        self.devices = []
        for section in self.config.sections():
            self.devices.append(ControllerWidget(self.widgetsFrame,
            "settings.ini", section))
            # plot sensor values
            cd = self.devices[-1] #  current device
            cd.line, = self.axes.plot([],[])

            # plot regulator values
            cd.regulator_line, = self.regulator_axis.plot([],[],'--')
            # get regulator limits
            tl, th = cd.controller.regulator.get_limits()
            # display temp limits 
            cd.reg_high, = self.regulator_axis.plot([-1e30,
                1e30],[th, th],'--', label='high lim')
            cd.reg_low , = self.regulator_axis.plot([-1e30,
                1e30],[tl, tl], '--',label='low lim')
            cd.sens_high_line, =\
            self.axes.plot([-1e30,1e30],[0,0])
            cd.sens_low_line, =\
            self.axes.plot([-1e30,1e30],[0,0])

#             self.axes.legend()
            self.regulator_axis.legend(['sig','hi','lo'], loc=3,
                    shadow=True, title="regulators")
            self.axes.legend(["sig", "hi", "lo"], loc=2, shadow=True,
                    title="Sensors")
            self.canvas.draw()



    def startMainLoop(self):
        self.root.after(1000, self.updateVariables)
        self.root.after(1000,self.updateGraph)
        Tk.mainloop()

    def updateVariables(self):
       """ Update the variables for every feedback loop """
       for device in self.devices:
           device.processWidgets()
           device.updateData()

    def updateGraph(self):
        """ Update the graph, for every item """
        self.updateVariables()

        for device in self.devices:
#             self.axes.plot(device.time_axis, device.sensor_axis)
            # update graph data
            device.line.set_xdata(np.array(device.time_axis) - self.t0)
            device.line.set_ydata(np.array(device.sensor_axis))

            device.regulator_line.set_xdata(np.array(device.time_axis)-self.t0)
            device.regulator_line.set_ydata(np.array(device.regulator_axis))


            self.axes.set_xlim(0, max(device.time_axis)-self.t0)

            # update controller lines
            tl, th = device.controller.regulator.get_limits()
            device.reg_low.set_ydata([tl, tl])
            device.reg_high.set_ydata([th, th])
            self.regulator_axis.set_ylim(tl - 0.5, th + 0.5)
            
            dc = device.controller 
            # sensor 
            sensmax, sensmin = dc.max_signal, dc.min_signal 
            senshigh, senslow = device.controller.max_signal, device.controller.sensor_low 
            print "Sensor low and high: ", senslow, senshigh
            self.axes.set_ylim(senslow , senshigh)
            device.sens_low_line.set_ydata([sensmin]*2)
            device.sens_high_line.set_ydata([sensmax]*2)

        try:
            self.canvas.draw()
        except:
            print "Drawing failed"

        self.root.after(1000, self.updateGraph)



if __name__ == '__main__':
    app = RootWindow()
# Show the graphs

# load in configuration file:
# for every section create a new regulator object

# update graphs every 2 seconds



