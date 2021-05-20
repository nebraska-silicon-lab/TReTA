#!/usr/bin/python3

import sys
import os
import time
import logging
import random
from collections import deque
from queue import Queue
from threading import Thread
import serial

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

import numpy as np

import PyQt5
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc


VIRTUAL_HARDWARE = False
CHANNELS = ["Ch0", "Ch1", "Ch2", "Ch3"]
CHANNELS_SELECT = [2, 3]  # index into CHANNELS
SAMPLE_PERIOD_SECONDS = .1 #seconds
SAMPLE_HISTORY_SIZE = 500

ARDUINO_SERIAL_PORT = 'COM3'
ARDUINO_SERIAL_BAUD = 9600

KEITHLEY_SERIAL_PORT = ''

random.seed("DEADBEEF")
logging.basicConfig(filename="OvenControlV2.log", filemode='w',
                    format='%(asctime)s %(name)-30s %(levelname)-8s %(message)s',
                    level=logging.INFO)
rcParams.update({'figure.autolayout': True,
                 'text.usetex': False,
                 'font.size': 8})


class DynamicPlot(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100,
                 n_plots=1, n_data=10, labels=None,
                 x_range=(0, 10), y_range=(0, 50),
                 title="", x_label="", y_label=""):
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.title = title
        self.x_range = x_range
        self.y_range = y_range
        self.n_plots = n_plots

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.updateGeometry(self)
        self.lines = []
        xs_strt = [x_range[0]+(x_range[1]-x_range[0])*i/n_data for i in range(n_data)]
        ys_strt = [(y_range[0]+y_range[1])/2]*n_data
        for i in range(n_plots):
            line, = self.axes.plot(xs_strt, ys_strt, label=labels[i])
            self.lines.append(line)
        self.axes.set_xlim(x_range)
        self.axes.set_ylim(y_range)
        self.axes.set_title(self.title)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.legend()
        self.fig.canvas.draw()

    def set_lims(self, xlim, ylim):
        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)
        self.fig.canvas.draw()

    def update_figure(self, xs, ys):
        for i, (x, y) in enumerate(zip(xs, ys)):
            self.lines[i].set_data(x, y)
        self.figure.canvas.draw()


class TretaDaq(qtw.QMainWindow):

    def __init__(self):
        super().__init__()
        logging.info("Application starting up")
        self.data_queue = Queue()
        self.init_gui()
        self.init_lookup()
        self.temperature_current = 0
        self.history_measured = [deque([0]*SAMPLE_HISTORY_SIZE, SAMPLE_HISTORY_SIZE) for _ in CHANNELS]

        if not VIRTUAL_HARDWARE:
            logging.info(f'Trying to connect to: {ARDUINO_SERIAL_PORT} at {ARDUINO_SERIAL_BAUD} BAUD.')
            try:
                self.serial_connection = serial.Serial(ARDUINO_SERIAL_PORT, ARDUINO_SERIAL_BAUD, timeout=4)
                logging.info(f'Connected to: {ARDUINO_SERIAL_PORT} at {ARDUINO_SERIAL_BAUD} BAUD.')
            except:
                logging.error(f'Failed to connect to: {ARDUINO_SERIAL_PORT} at {ARDUINO_SERIAL_BAUD} BAUD.')
            self.serial_connection.reset_input_buffer()

        self.closed = False
        self.ser_thread = Thread(target=self.serial_read_thread)
        self.ser_thread.start()

        self.timer = qtc.QBasicTimer()
        self.timer.start(int(1000*SAMPLE_PERIOD_SECONDS), self)

    def init_gui(self):
        # Graph Area(Left)
        self.monitor_cycle_graph = DynamicPlot(n_plots=len(CHANNELS_SELECT), n_data=SAMPLE_HISTORY_SIZE,
                                               labels=[CHANNELS[idx] for idx in CHANNELS_SELECT],
                                               x_range=(0, SAMPLE_HISTORY_SIZE*SAMPLE_PERIOD_SECONDS),
                                               x_label="time(s)", y_label="Temperature(deg C)",
                                               y_range=(0, 50),
                                               title="Temperature Monitor")

        ga = qtw.QWidget()
        ga_layout = qtw.QVBoxLayout()
        ga_layout.addWidget(self.monitor_cycle_graph)
        ga.setLayout(ga_layout)

        # Info area
        self.t1 = qtw.QLabel("No Data")
        self.t2 = qtw.QLabel("No Data")
        self.delta_t = qtw.QLabel("No Data")

        font = self.t1.font()
        font.setPointSizeF(10.0)
        self.t1.setFont(font)
        self.t2.setFont(font)
        self.delta_t.setFont(font)

        # Info area layout
        ia = qtw.QWidget()
        ia_layout = qtw.QGridLayout()
        ia_layout.addWidget(self.t1, 0, 0, 3, 1)
        ia_layout.addWidget(self.t2, 1, 0, 3, 1)
        ia_layout.addWidget(self.delta_t, 2, 0, 3, 1)
        ia.setLayout(ia_layout)

        # Control area
        # self.power_set = qtw.QLineEdit()
        # self.power_set.setText("Hello World")
        # self.power_set.setFont(font)

        # Control area layout
        ca = qtw.QWidget()
        ca_layout = qtw.QGridLayout()
        # ca_layout.addWidget(self.power_set, 0, 0, 1, 1)
        ca.setLayout(ca_layout)



        # right panel
        rp = qtw.QSplitter()
        rp.setOrientation(PyQt5.QtCore.Qt.Orientation.Vertical)
        rp.addWidget(ia)
        rp.addWidget(ca)

        # Main Widget Setup
        main = qtw.QSplitter()
        main.addWidget(ga)
        main.addWidget(rp)
        self.setCentralWidget(main)

        self.center()
        self.setWindowTitle('TReTA DAQ')
        self.show()

    def init_lookup(self):
        def therm_resistance(t):
            t_K = t + 273.15
            R_ref = 10_000
            A = -14.6337
            B = 4791.842  # K
            C = -115334  # K^2
            D = -3.730535E6  # K^3
            return R_ref * np.exp(A + B / t_K + C / t_K ** 2 + D / t_K ** 3)
        temps = np.linspace(0, 80, 10000)
        res = therm_resistance(temps)
        res_par = 1.0 / (1.0 / 5_000 + 1.0 / res)
        res_cir = 5_000 + res_par
        current = 5.0 / res_cir
        self.sense_voltage = current * res_par
        self.sense_temps = temps

    def convert_volts_to_degrees(self, volts, sensor_id = None):
        idx = np.argmax(self.sense_voltage < volts)
        return self.sense_temps[idx]

    def center(self):
        screen = qtw.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.resize(screen.width()//2, screen.height()//2)
        self.move((screen.width()-size.width())//2,
                  (screen.height()-size.height())//2)

    def update_temperature(self):
        while not self.data_queue.empty():
            voltages = self.data_queue.get()
            for l, d in zip(self.history_measured, voltages):
                temperature = self.convert_volts_to_degrees(d)
                logging.info(f"Temp Reading: {temperature:.2f}")
                l.append(temperature)

    def update_ui(self):
        # self.current_temp_label.setText("Current: {:.2f}°C"
        #                                 .format(self.temperature_current))
        plot_times = [i*SAMPLE_PERIOD_SECONDS for i in range(SAMPLE_HISTORY_SIZE)]
        self.monitor_cycle_graph.update_figure([[plot_times]]*len(CHANNELS_SELECT),
                                               [self.history_measured[idx] for idx in CHANNELS_SELECT])

        t1 = self.history_measured[CHANNELS_SELECT[0]][-1]
        t2 = self.history_measured[CHANNELS_SELECT[1]][-1]
        dt = abs(t1 - t2)
        self.t1.setText(f"T1: {t1:.2f} °C")
        self.t2.setText(f"T2: {t2:.2f} °C")
        self.delta_t.setText(f"dT: {dt:.2f} °C")

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            self.update_temperature()
            self.update_ui()
        else:
            super().timerEvent(event)

    def keyPressEvent(self, a0: PyQt5.QtGui.QKeyEvent) -> None:
        if a0.nativeVirtualKey() == 27:  # esc
            self.close()
        else:
            super().keyPressEvent(a0)

    def closeEvent(self, event):
        logging.info("Application shutting down. Bye!")
        self.closed = True

    def serial_read_thread(self):
        while True:
            if self.closed:
                break
            if VIRTUAL_HARDWARE:
                self.data_queue.put([random.gauss(2, 1) for _ in CHANNELS])
                time.sleep(.5)
            else:
                line = self.serial_connection.readline().decode('ascii')
                logging.info(line)
                vs = [float(t) for t in line.split(" ")]
                self.data_queue.put(vs)
        if not VIRTUAL_HARDWARE:
            self.serial_connection.close()


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    oc = TretaDaq()
    sys.exit(app.exec_())
