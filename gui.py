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
    canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

    button = Tk.Button(master=root, text='update', command=updategraph)
    button.pack(side=Tk.BOTTOM)
    Tk.mainloop()

