import matplotlib
matplotlib.use('TkAgg')

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,\
NavigationToolbar2TkAgg
from matplotlib.figure import Figure

import sys
if sys.version_info[0] < 3:
    import Tkinter as Tk
else:
    import tkinter as Tk


# worker Thread

import threading
import time


class DataGenerator(threading.Thread):
    def __init__(self):
        """ Create variables"""
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.x = np.array([0])
        self.y = np.array([2])

    def run(self):
        while True:
            time.sleep(0.4)
            self.x = np.append(self.x, self.x[-1]+1)
            self.y = np.append(self.y, np.random.rand())
            print "%d, %f" % (self.x[-1] , self.y[-1])


def destroy(e): sys.exit(0)


def updategraph():
    for lines in zip(datagen.x, datagen.y):
        print lines
    # update graph
    line.set_ydata(datagen.y)
    line.set_xdata(datagen.x)

    a.set_xlim(min(datagen.x), max(datagen.x))
    canvas.draw()

def labelWithEntry(parent, labeltext, row, startcol, **kwargs):
    entry = Tk.Entry(master=parent, **kwargs)
    label = Tk.Label(text=labeltext)
    label.grid(row=row, column=startcol)
    entry.grid(row=row, column=startcol+1)

    return label, entry



if __name__ == '__main__':
    datagen = DataGenerator()
    datagen.start()
    root = Tk.Tk()
    root.wm_title("Embedding TK")
    
    # figure
    f = Figure(figsize=(5, 4), dpi=100)
    a = f.add_subplot(111)

    # signal
    t = np.linspace(0, 6.24, 1000)
    s = np.sin(t)

    line, = a.plot(t, s)
    a.set_title("TK embedding")

    # drawing area
    canvas = FigureCanvasTkAgg(f, master=root)
    canvas.show()
    canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

    # toolbar
    toolbar = NavigationToolbar2TkAgg(canvas, root)
    toolbar.update()
    canvas._tkcanvas.pack(side=Tk.TOP, expand=1)

    # widget for feedback
    frame = Tk.LabelFrame(root, text="Feedback_1")
    frame.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

    startbutton = Tk.Button(master=frame, text="Start", command=updategraph)
    startbutton.grid(row=1,column=1)

    stopbutton = Tk.Button(master=frame, text="Stop", command=updategraph)
    stopbutton.grid(row=1,column=2)

    lockSwitch = Tk.Checkbutton(master=frame, text="Lock")
    lockSwitch.grid(row=1, column=3)

    Tk.Label(master=frame, text="Max T").grid(row=2, column=1)
    max_value_regulator_field = Tk.Entry(master=frame, width=5)
    max_value_regulator_field.grid(row=2,column=2)

    max_value_regulator_field.insert(0,2)
    Tk.Label(master=frame, text="Min T").grid(row=2, column=3)
    min_value_regulator_field = Tk.Entry(master=frame, width=5)
    min_value_regulator_field.grid(row=2,column=4)
    
    Tk.Label(master=frame,text="Max sensor").grid(row=2, column=5)
    max_value_sensor_field = Tk.Entry(master=frame, width=5)
    max_value_sensor_field.grid(row=2, column=6)

    Tk.Label(master=frame, text="Min sensor").grid(row=2, column=7)
    min_value_sensor_field = Tk.Entry(master=frame, width=5)
    min_value_sensor_field.grid(row=2, column=8)


    Tk.mainloop()

