import scipy

import pyqtgraph as pg
import time

import numpy as np


from dataclasses import dataclass
from PySide6.QtCore import QObject, Slot, QTimer, QFile
from PySide6.QtWidgets import QWidget, QApplication, QGraphicsEllipseItem
from gui_utils import SerialIOHandler, BluetoothControllerHandler, LowPassFilter, RxPacket, TxPacket, BluetoothPacket
import queue

import pygame
import sys


generated_class, base_class = pg.Qt.loadUiType("bluetooth.ui")


class PlotView(base_class, generated_class):
    """model view controller framework view,
    imports UI from testing.ui"""

    def __init__(self, y_range=(-10, 380), title="Real-Time Data"):
        super().__init__()
        self.setupUi(self)

        self.radial_left.setXRange(-1.03, 1.03)
        self.radial_left.setYRange(-1.03, 1.03)
        self.radial_left.showGrid(x=False, y=False)
        self.radial_left.hideAxis("bottom")
        self.radial_left.hideAxis("left")

        self.radial_right.setXRange(-1.03, 1.03)
        self.radial_right.setYRange(-1.03, 1.03)
        self.radial_right.showGrid(x=False, y=False)
        self.radial_right.hideAxis("bottom")
        self.radial_right.hideAxis("left")

        cm = pg.colormap.get("inferno")  # prepare a linear color map
        cm.reverse()  # reverse it to put light colors at the top
        span = (0.0, 1.0)
        # pen = cm.getPen(span=(0.0, 1.0), width=5)

        self.plot_left_knob = self.radial_left.plot(
            pen=pg.mkPen(color=(255, 0, 0), width=2),
            symbol="o",  # Use a circular symbol
            symbolBrush=(255, 0, 0),  # Fill color
            symbolSize=[0, 0, 5],
            name="js_left",
        )

        self.plot_left_knob_echo = self.radial_left.plot(
            pen=pg.mkPen(color=(0, 0, 255), width=2),
            symbol="o",  # Use a circular symbol
            symbolBrush=(0, 0, 255),  # Fill color
            symbolSize=[0, 0, 5],
            name="echo_left",
        )

        self.plot_right_knob = self.radial_right.plot(
            pen=pg.mkPen(color=(255, 0, 0), width=2),
            symbol="o",  # Use a circular symbol
            symbolBrush=(255, 0, 0),  # Fill color
            symbolSize=[0, 0, 5],
            name="js_right",
        )

        self.plot_right_knob_echo = self.radial_right.plot(
            pen=pg.mkPen(color=(0, 0, 255), width=2),
            symbol="o",  # Use a circular symbol
            symbolBrush=(0, 0, 255),  # Fill color
            symbolSize=[0, 0, 5],
            name="echo_right",
        )

        # echo linear plot
        self.plot_echo = self.linear_plot_widget.plot(
            pen=pg.mkPen(color=(0, 0, 255), width=2),
            name="echo1",
        )

        # command linear plot (pre filter)
        self.plot_command = self.linear_plot_widget.plot(
            pen=pg.mkPen(color=(255, 0, 0, 120), width=2),
            name="command1",
        )

        # self.plot_fft = self.fft_plot_widget.plot(
        #     pen=pg.mkPen(color=(255, 0, 0, 120), width=2),
        #     name="fft1",
        # )

    def update_bluetooth(self, bluetooth_data, speed1_scale, speed23_scale):

        axis0 = bluetooth_data["left_horiz"][-3:]
        axis1 = -bluetooth_data["left_vert"][-3:]
        axis2 = bluetooth_data["right_horiz"][-3:]
        axis3 = -bluetooth_data["right_vert"][-3:]

        self.plot_left_knob.setData(axis0, axis1)
        self.plot_right_knob.setData(axis2, axis3)
        self.plot_command.setData(
            bluetooth_data["timestamp"], (-bluetooth_data["left_vert"] * speed1_scale).astype(int)
        )

    def update_fft(self, fft_tuple):
        length = len(fft_tuple[0]) / 2
        # fft_freq, fft_data = fft_tuple

        # self.plot_fft.setData(fft_freq, fft_data)

    def update_serial(self, rx_data, speed0_scale, speed1_scale, speed23_scale):

        self.plot_echo.setData(rx_data["timestamp"], -rx_data["echo_stepper1"])
        self.plot_left_knob_echo.setData(
            rx_data["echo_stepper0"][-3:] / (speed0_scale + 0.01),
            -rx_data["echo_stepper1"][-3:] / (speed1_scale + 0.01),
        )

        transform_data = rx_data["echo_stepper2"][-3:] + 1j * rx_data["echo_stepper3"][-3:]

        transform_data *= (0.7 - 0.7j) / (speed23_scale + 0.01)

        self.plot_right_knob_echo.setData(-np.real(transform_data), np.imag(transform_data))

        # self.plot_right_knob_echo.setData(
        #     rx_data["echo_stepper2"][-3:] * 1.0 / (8.0 * 600.0), rx_data["echo_stepper3"][-3:] * 1.0 / (8.0 * 600.0)
        # )

    def update_labels(self):
        self.speed0_label.setText(f"Speed0: {self.speed0_scale_dial.value()}")
        self.speed1_label.setText(f"Speed1: {self.speed1_scale_slider.value()}")
        self.speed23_label.setText(f"Speed23: {self.speed23_scale_slider.value()}")
        self.acceleration_label.setText(f"Accel: {self.acceleration_slider.value()}")


class Controller(QObject):
    def __init__(self, model, view):
        super().__init__()
        self.model = model
        self.view = view

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start(15)

        self.tx_timer = QTimer(self)
        self.tx_timer.start(30)
        self.tx_timer.timeout.connect(self.model.send_packet)

        self.view.acceleration_slider.setValue(self.model.acceleration)
        self.view.speed0_scale_dial.setValue(self.model.speed0_scale)
        self.view.speed1_scale_slider.setValue(self.model.speed1_scale)
        self.view.speed23_scale_slider.setValue(self.model.speed23_scale)

        self.view.update_labels()

        self.view.acceleration_slider.valueChanged.connect(self.slider_changed)
        self.view.speed0_scale_dial.valueChanged.connect(self.slider_changed)
        self.view.speed1_scale_slider.valueChanged.connect(self.slider_changed)
        self.view.speed23_scale_slider.valueChanged.connect(self.slider_changed)

    def slider_changed(self):

        self.view.update_labels()

        self.model.speed0_scale = self.view.speed0_scale_dial.value()
        self.model.speed1_scale = self.view.speed1_scale_slider.value()
        self.model.speed23_scale = self.view.speed23_scale_slider.value()
        self.model.acceleration = self.view.acceleration_slider.value()

    def on_timer_tick(self):

        # self.view.update_fft(self.model.update_fft())

        bluetooth_data = self.model.get_bluetooth_data()
        echo_data = self.model.get_serial_data()

        self.view.update_bluetooth(bluetooth_data, self.model.speed1_scale, self.model.speed23_scale)
        self.view.update_serial(echo_data, self.model.speed0_scale, self.model.speed1_scale, self.model.speed23_scale)

        self.view.state_label.setText(f"state: {self.model.echoed_speed:.2f}")


class Model(QObject):

    def __init__(self):
        super().__init__()

        self.mcu_state = "NODATA"
        self.echoed_speed = 0
        self.prev_time = 0
        self.io_handler = SerialIOHandler(baudrate=115200)

        # bluetooth dtype can be found in bluetoothhandler. just has joystick axis data
        self.bluetooth_buffer = CircularBuffer(size=118, dtype=BluetoothPacket.bluetooth_dtype)

        self.serial_rx_buffer = CircularBuffer(size=256, dtype=RxPacket.serial_rx_dtype)

        self.io_handler.new_data.connect(self.update)

        self.io_handler.find_ports()
        if self.io_handler.try_ports() is True:
            self.io_handler.start()
            self.sync_times = self.io_handler.get_start_times()
        else:
            print("no usb port penis")
            self.io_handler.start_sim()

        self.bluetooth_handler = BluetoothControllerHandler(start_time=self.sync_times.host_ms)
        self.bluetooth_handler.new_bluetooth_data.connect(self.update_bluetooth)
        self.bluetooth_handler.start()

        self.sync_offset = self.sync_times.get_offset()
        print(self.sync_offset)

        self.speed0_scale = 3 * 800 * 8
        self.speed1_scale = 800 * 8
        self.speed23_scale = 800 * 8
        self.acceleration = 50000

    def update(self):

        # this direction logic is to give more intuitive control to motors 2 and 3.

        while (rx_packet := self.io_handler.rx_next_packet()) is not None:
            rx_packet_arr = rx_packet.as_array()

            rx_packet_arr["timestamp"] = rx_packet_arr["timestamp"] - self.sync_times.mcu_ms

            self.serial_rx_buffer.push(rx_packet_arr)

    def update_fft(self):
        sampling_rate = 200
        num_samples = 256
        fft_freq = scipy.fft.fftfreq(num_samples, 1 / sampling_rate)
        fft_data = scipy.fft.fftshift(np.abs(scipy.fft.fft(self.get_serial_data()["echo_stepper1"])))
        return (fft_freq, fft_data)

    def get_serial_data(self):

        return self.serial_rx_buffer.get_all()

    def update_bluetooth(self):

        # empty bluetooth queue into circular buffer
        # walrus operator is evaluation and asignment aT THE SAME TIME
        while (sample := self.bluetooth_handler.get_next_bluetooth_sample()) is not None:
            sample["timestamp"] = sample["timestamp"] - self.sync_times.host_ms + 96
            self.bluetooth_buffer.push(sample)

    def get_bluetooth_data(self):

        return self.bluetooth_buffer.get_all()

    def send_packet(self, speed0=0, speed1=0, speed2=0, speed3=0):

        bluetooth_latest = self.bluetooth_buffer.get_latest()

        # more intuitive control
        vert_portion = bluetooth_latest["right_vert"] / 1.4
        horiz_portion = -bluetooth_latest["right_horiz"] / 1.4

        speed0 = bluetooth_latest["left_horiz"]
        speed1 = bluetooth_latest["left_vert"]
        speed2 = vert_portion + horiz_portion
        speed3 = -vert_portion + horiz_portion

        # self.filtered_speed1 = speed1

        tx_packet = TxPacket()
        tx_packet.commanded_speed_stepper0 = int(self.speed0_scale * speed0)
        tx_packet.commanded_speed_stepper1 = int(self.speed1_scale * speed1)
        tx_packet.commanded_speed_stepper2 = int(self.speed23_scale * speed2)
        tx_packet.commanded_speed_stepper3 = int(self.speed23_scale * speed3)
        tx_packet.commanded_max_acceleration = self.acceleration

        self.io_handler.queue_latest_tx(tx_packet)


class CircularBuffer:
    def __init__(self, size, dtype):
        self.buffer = np.zeros(size, dtype=dtype)
        self.index = -1
        self.size = size

    def push(self, val):
        self.index = (self.index + 1) % self.size
        self.buffer[self.index] = val

    def get_latest(self):

        return self.buffer[self.index]

    def get_all(self):

        return np.roll(self.buffer, -self.index - 1)


def application():
    import sys

    app = QApplication(sys.argv)
    model = Model()
    view = PlotView()
    controller = Controller(model, view)

    view.show()

    sys.exit(app.exec())  # Run Qt event loop


if __name__ == "__main__":
    import cProfile
    import pstats
    import signal

    application()
    # signal.signal(signal.SIGINT, signal.SIG_DFL)
    # cProfile.run("application()", "profile_output.prof")
    # p = pstats.Stats("profile_output.prof")
    # p.sort_stats("cumulative").print_stats(20)  # Print top 10 cumulative time functions
