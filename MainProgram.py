# import statements
import matplotlib
matplotlib.use('TkAgg')
import Queue
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,\
NavigationToolbar2TkAgg
from matplotlib.figure import Figure

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
        self.root = Tk.Tk()
        self.root.wm_title("Embedding TK")

    def setupGraph(self):
        """ Setup a graph in the window"""
        # create frame to put figure in
        self.figureframe = Tk.Frame(self.root)
        self.figureframe.grid()
        # create figure
        self.figure = Figure(figsize=(5,4), dpi=75)
        self.axes = self.figure.add_subplot(111)

        # canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.figureframe)
        self.canvas.get_tk_widget().pack(side=Tk.TOP, expand=False)
        self.canvas.show()

        # toolbar
        toolbar = NavigationToolbar2TkAgg(self.canvas, self.figureframe)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=Tk.TOP, expand=False)

    def addWidgets(self):
        # create a frame to put all the widgets in.
        self.widgetsFrame = Tk.LabelFrame(self.root, text="Widgets")
        self.widgetsFrame.grid(row=3, sticky='EW')
        #  add a button inside
        self.button = Tk.Checkbutton(self.widgetsFrame,text="Bla")
        self.button.pack(side=Tk.TOP)

        from feedback import ControllerWidget
        self.controllerWidget = ControllerWidget(
                                self.widgetsFrame,
                                "settings.ini", 
                                "Baseplate")

        self.time_axis = []
        self.temp_axis = []
        self.sensor_axis = []

    def startMainLoop(self):
        self.root.after(1000,self.updateGraph)
        Tk.mainloop()

    def updateGraph(self):
        """ Update the graph, for every item """
        print "Updating graph"
        self.root.after(1000, self.updateGraph)
        try:
            self.time_axis.append(self.controllerWidget.controller.time_queue.get_nowait())
        except Queue.Empty:
            pass
        print self.time_axis




if __name__ == '__main__':
    app = RootWindow()
# Show the graphs

# load in configuration file:
# for every section create a new regulator object

# update graphs every 2 seconds



