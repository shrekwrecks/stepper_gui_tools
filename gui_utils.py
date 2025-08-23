import time
import numpy as np
import scipy
from dataclasses import dataclass, field
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QFile
from PySide6.QtWidgets import QWidget, QApplication
import threading
import serial
from construct import Float32l, Int32ul, Int32sl, this, Struct, Enum
from cobs import cobs
import queue
from collections import namedtuple
import serial.tools.list_ports
import pygame
from typing import ClassVar


SystemStateField = Enum(Int32sl, OK=0, ENCODER_ERROR=1, MOTOR_ERROR=2, UNKNOWN=99)


@dataclass
class SyncTimes:
    mcu_ms: int
    host_ms: int

    def get_offset(self):
        return self.host_ms - self.mcu_ms


@dataclass(slots=True)
class TxPacket:
    commanded_speed_stepper0: int = 0
    commanded_speed_stepper1: int = 0
    commanded_speed_stepper2: int = 0
    commanded_speed_stepper3: int = 0
    commanded_max_acceleration: int = 10000

    _struct: ClassVar[Struct] = Struct(
        "commanded_speed_stepper0" / Int32sl,  # steps per seocnd
        "commanded_speed_stepper1" / Int32sl,  # steps per seocnd
        "commanded_speed_stepper2" / Int32sl,  # steps per seocnd
        "commanded_speed_stepper3" / Int32sl,  # steps per seocnd
        "commanded_max_acceleration" / Int32sl,  # steps per seocnd per second
    )

    def to_bytes(self):
        return self._struct.build(
            {
                # "timestamp": 0,  # Current ms timestamp
                "commanded_speed_stepper0": int(self.commanded_speed_stepper0),
                "commanded_speed_stepper1": int(self.commanded_speed_stepper1),
                "commanded_speed_stepper2": int(self.commanded_speed_stepper2),
                "commanded_speed_stepper3": int(self.commanded_speed_stepper3),
                "commanded_max_acceleration": int(self.commanded_max_acceleration),
            }
        )


@dataclass(slots=True, frozen=True)
class BluetoothPacket:
    timestamp: int = 0
    left_horiz: float = 0.0
    left_vert: float = 0.0
    right_horiz: float = 0.0
    right_vert: float = 0.0

    bluetooth_dtype = np.dtype(
        [
            ("timestamp", np.int32),
            ("left_horiz", np.float32),
            ("left_vert", np.float32),
            ("right_horiz", np.float32),
            ("right_vert", np.float32),
        ]
    )

    @classmethod
    def from_joystick(cls, js, timestamp):
        return cls(
            timestamp=timestamp,
            left_horiz=js.get_axis(0),
            left_vert=js.get_axis(1),
            right_horiz=js.get_axis(2),
            right_vert=js.get_axis(3),
        )

    def as_array(self):
        return np.array(
            (
                self.timestamp,
                self.left_horiz,
                self.left_vert,
                self.right_horiz,
                self.right_vert,
            ),
            dtype=self.bluetooth_dtype,
        )


@dataclass(slots=True, frozen=True)
class RxPacket:
    timestamp: int = 0
    echo_stepper0: int = 0
    echo_stepper1: int = 0
    echo_stepper2: int = 0
    echo_stepper3: int = 0
    encoder_angle: int = 0
    open_loop_angle: int = 0
    state: Enum = 0

    # class-level compiled Struct
    _struct: ClassVar[Struct] = Struct(
        "timestamp" / Int32ul,
        "echo_stepper0" / Int32sl,
        "echo_stepper1" / Int32sl,
        "echo_stepper2" / Int32sl,
        "echo_stepper3" / Int32sl,
        "encoder_angle" / Int32sl,
        "open_loop_angle" / Int32sl,
        "state" / SystemStateField,  # or your SystemStateField
    ).compile()

    serial_rx_dtype: ClassVar[np.dtype] = np.dtype(
        [
            ("timestamp", np.uint32),
            ("echo_stepper0", np.int32),
            ("echo_stepper1", np.int32),
            ("echo_stepper2", np.int32),
            ("echo_stepper3", np.int32),
            ("encoder_angle", np.int32),
            ("open_loop_angle", np.int32),
            ("state", np.uint8),
        ]
    )

    @classmethod
    def from_bytes(cls, raw_bytes):
        # can consider adding parsing time or reading from timestamp
        parsed = cls._struct.parse(raw_bytes)
        return cls(
            timestamp=parsed.timestamp,
            echo_stepper0=parsed.echo_stepper0,
            echo_stepper1=parsed.echo_stepper1,
            echo_stepper2=parsed.echo_stepper2,
            echo_stepper3=parsed.echo_stepper3,
            encoder_angle=parsed.encoder_angle,
            open_loop_angle=parsed.open_loop_angle,
            state=parsed.state,
        )

    def as_array(self):
        return np.array(
            (
                self.timestamp,
                self.echo_stepper0,
                self.echo_stepper1,
                self.echo_stepper2,
                self.echo_stepper3,
                self.encoder_angle,
                self.open_loop_angle,
                self.state,
            ),
            dtype=self.serial_rx_dtype,
        )

    @classmethod
    def sizeof(cls):
        return cls._struct.sizeof()


class BluetoothControllerHandler(QObject):

    bluetooth_dtype = np.dtype(
        [
            ("timestamp", np.int32),
            ("left_horiz", np.float32),
            ("left_vert", np.float32),
            ("right_horiz", np.float32),
            ("right_vert", np.float32),
        ]
    )

    new_bluetooth_data = Signal()

    def __init__(self, start_time):
        super().__init__()
        pygame.init()

        self.running = False
        self.thread = None
        self.joystick = None

        self.axes = {}
        self.buttons = {}
        self.start_time = start_time

        self.try_connect()
        self.q = queue.Queue(maxsize=5)

    def try_connect(self):

        pygame.joystick.quit()
        self.joystick = None
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print("No joystick detected")
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Joystick initialized: {self.joystick.get_name()}")
            self.joystick.rumble(1, 1, 300)
            time.sleep(0.3)
            self.joystick.stop_rumble()

    def poll_joystick(self):
        while self.running:
            if not self.joystick:
                time.sleep(0.1)
                continue

            pygame.event.pump()
            current_event = BluetoothPacket.from_joystick(js=self.joystick, timestamp=(time.monotonic_ns()) / 1000000)

            try:
                self.q.put_nowait(current_event.as_array())
            except queue.Full:
                _ = self.q.get_nowait()  # remove the old item
                self.q.put_nowait(current_event.as_array())

            self.new_bluetooth_data.emit()

            time.sleep(0.01)

    def get_next_bluetooth_sample(self):
        try:
            return self.q.get_nowait()
        except queue.Empty:
            return None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.poll_joystick, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()


class SerialIOHandler(QObject):

    new_data = Signal()  # really its a Struct

    def __init__(self, baudrate: int = 115200):
        super().__init__()
        self.baudrate: int = baudrate
        self.rx_q = queue.Queue(maxsize=256)
        self.tx_q = queue.Queue(maxsize=1)  # latest message only
        self.running = False
        self.thread = None
        self.buf = bytearray()

    def find_ports(self):
        possible_ports = serial.tools.list_ports.comports(include_links=False)
        self.usb_ports = [
            p.device
            for p in possible_ports
            if "COM" in p.device.upper() or "TTYUSB" in p.device.upper() or "TTYACM" in p.device.upper()
        ]

    def try_ports(self):
        for usb_port in self.usb_ports:
            ser = serial.Serial(port=usb_port, baudrate=self.baudrate, timeout=0.1)
            time.sleep(0.1)
            packet = self.read_packet(ser)
            if packet is None:
                ser.close()
                continue
            else:
                try:
                    decoded = self.decode_packet(packet)
                except cobs.DecodeError:
                    return False

                self.mcu_start_time = decoded.timestamp
                self.computer_start_time = time.monotonic_ns()

                self.port = usb_port
                self.ser = ser
                return True

        self.port = None
        self.ser = None
        return False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.read_and_send_loop, daemon=True)
        self.thread.start()

    def start_sim(self):
        self.running = True

        self.init_time = int(time.time() * 1000)
        self._sim_prev_angle = 0.0
        self._sim_prev_open_loop_angle = 0.0
        self.latest_tx = TxPacket()

        self.thread = threading.Thread(target=self.sim_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if hasattr(self, "ser") and self.ser.is_open:
            self.ser.close()

    def get_start_times(self) -> SyncTimes:
        return SyncTimes(self.mcu_start_time, self.computer_start_time / 1000000)

    def read_and_send_loop(self):

        while self.running:
            packet = self.read_packet(self.ser)
            parsed = self.decode_packet(packet)

            try:
                self.rx_q.put_nowait(parsed)
                self.new_data.emit()
            except:
                pass

            if tx_packet := self.get_next_tx():
                self.send(tx_packet)

    def read_packet(self, ser: serial.Serial):

        i = self.buf.find(b"\x00")
        if i >= 0:
            packet = self.buf[:i]
            self.buf = self.buf[i + 1 :]
            return packet
        while True:
            i = max(1, min(2048, ser.in_waiting))
            data = ser.read(i)
            i = data.find(b"\x00")
            if i >= 0:
                packet = self.buf + data[:i]
                self.buf[0:] = data[i + 1 :]
                return packet
            else:
                self.buf.extend(data)

    def rx_next_packet(self):
        try:
            return self.rx_q.get_nowait()
        except queue.Empty:
            return None

    def get_next_tx(self):
        try:
            return self.tx_q.get_nowait()
        except queue.Empty:
            return None

    def queue_latest_tx(self, data_struct):
        try:
            self.tx_q.get_nowait()  # discard oldest item if any
        except queue.Empty:
            pass  # queue was already empty
        self.tx_q.put_nowait(data_struct)

    def decode_packet(self, packet):

        try:
            decoded = cobs.decode(packet)

            if len(decoded) != RxPacket.sizeof():
                print(
                    f"Invalid packet size: {len(decoded)} expects: {RxPacket.sizeof()}. Packet: ",
                    packet,
                )
                return
            # consider eventually moving away from construct to pure numpy structured arrays
            # faster plus probably more maintainable since only 1 definition
            parsed = RxPacket.from_bytes(decoded)

            # ive just added this try except without testing it.
            return parsed

        except cobs.DecodeError:
            print(f"COBS decode error: ", packet)

    def send(self, tx_packet):
        if not hasattr(self, "ser") or self.ser is None or not self.ser.is_open:
            print("Serial port not open")
            return

        try:
            # print("send")
            packed = tx_packet.to_bytes()
            encoded = cobs.encode(packed) + b"\x00"  # COBS delimiter
            self.ser.write(encoded)
        except Exception as e:
            print(f"Error sending packet: {e}")

    def sim_loop(self):
        time.sleep(0.3)

        while self.running:
            if tx_packet := self.get_next_tx():
                self.latest_tx = tx_packet
                # print(tx_packet)
            self.simulate_packet()
            # self.decode_packet(packet)

    def simulate_packet(self):

        now = int(time.time() * 1000) - self.init_time

        error = self._sim_prev_angle - self._sim_prev_open_loop_angle

        raw_bytes = RxPacket._struct.build(
            dict(
                timestamp=now,
                echo_stepper1=self.latest_tx.commanded_speed_stepper1
                + int(float(abs(360 * np.cos(now / 1000)) + np.random.uniform(-7, 16))),
                echo_stepper2=self.latest_tx.commanded_speed_stepper2,
                echo_stepper3=self.latest_tx.commanded_speed_stepper3,
                encoder_angle=0,
                open_loop_angle=int(self._sim_prev_open_loop_angle + error / 5),
                state=0,
            )
        )

        parsed = RxPacket.from_bytes(raw_bytes)

        self.sim_prev_angle = parsed.echo_stepper1
        self._sim_prev_open_loop_angle = parsed.open_loop_angle

        self.rx_q.put_nowait(parsed)
        self.new_data.emit()
        time.sleep(0.003)


class LowPassFilter:
    def __init__(self, cutoff_hz, fs_hz, order=2):
        # Normalized cutoff frequency (Nyquist = fs/2)
        nyq = fs_hz / 2.0
        norm_cutoff = cutoff_hz / nyq

        # bessel design
        self.b, self.a = scipy.signal.bessel(order, norm_cutoff, btype="low", analog=False, norm="phase")

        # Internal filter state for lfilter_zi (so it behaves properly sample-by-sample)
        self.zi = scipy.signal.lfilter_zi(self.b, self.a)

    def process(self, x):
        # Run one sample through the IIR filter
        y, self.zi = scipy.signal.lfilter(self.b, self.a, [x], zi=self.zi)
        return y[0]
