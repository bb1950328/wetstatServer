# coding=utf-8
import random
import socket
import threading
import time
from typing import Dict

import gpiozero

from wetstat.common import config

COM_PORT: int = 34321
RES_PORT: int = 34322

ERROR: str = "ERROR"


class CounterServiceServer(object):

    def __init__(self) -> None:
        self.counters = self.CounterManager()

    class Counter(object):
        def __init__(self, pin: int):
            def callback_wrap() -> None:
                self._callback()

            self.pin: int = pin
            self.button = gpiozero.Button(pin, pull_up=None, active_state=True)
            self.button.when_activated = callback_wrap
            self.value: int = 0
            self.lock: threading.Lock = threading.Lock()

        def _callback(self) -> None:
            with self.lock:
                self.value += 1

        def get(self, reset=False) -> int:
            with self.lock:
                val = self.value
                if reset:
                    self.value = 0
                return val

        def get_and_reset(self) -> int:
            return self.get(reset=True)

        def destroy(self) -> None:
            self.lock.acquire()
            self.button.close()
            del self.pin, self.button, self.value, self.lock

    class FakeCounter(Counter):
        AVERAGE_SECONDS_PER_COUNT = 10

        def __init__(self, pin) -> None:
            self.value: int = 0
            self.last_access: float = time.time()
            self.lock: threading.Lock = threading.Lock()

        def get(self, reset=False) -> int:
            with self.lock:
                now = time.time()
                since_last = now - self.last_access
                pulses = int(random.gauss(1, 0.3) * (since_last / self.AVERAGE_SECONDS_PER_COUNT))
                self.value += pulses
                val = self.value
                if reset:
                    self.value = 0
                return val

    class CounterManager(object):
        def __init__(self) -> None:
            self.list_lock = threading.Lock()
            self.counters: Dict[int, CounterServiceServer.Counter] = {}

        def add_counter(self, pin, is_fake=False) -> None:
            with self.list_lock:
                counter_type = CounterServiceServer.FakeCounter if is_fake else CounterServiceServer.Counter
                self.counters[pin] = counter_type(pin)

        def remove_counter(self, pin: int) -> None:
            with self.list_lock:
                self.counters[pin].destroy()
                del self.counters[pin]

        def get_counter(self, pin: int):
            return self.counters[pin]

    def start(self, pin: int) -> None:
        self.counters.add_counter(pin, is_fake=not config.on_pi())

    def run_server(self) -> None:
        """
        :return: None
        listens on UDP port and sends back on UDP port+1
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.bind(("", COM_PORT))
            while True:
                data, (ip, port) = s.recvfrom(1 << 10)
                data = data.decode(errors="replace")
                res = self.handle_command(data)

                s.sendto(res.encode(), (ip, RES_PORT))

        finally:
            s.close()

    def handle_command(self, data: str) -> str:
        # noinspection PyBroadException
        try:
            res = "OK"
            pin = int(data.split(" ")[1])

            if data.startswith("get"):
                value = self.counters.get_counter(pin).get_and_reset()
                res = str(value)
            elif data.startswith("stop"):
                self.counters.remove_counter(pin)
            elif data.startswith("start"):
                self.start(pin)
            return res
        except Exception as e:
            return ERROR + ": (" + str(e) + ")"


req_socket = None
result_socket = None


def send_command(command: str) -> str:
    """
    :param command: look in wetstat.hardware.sensors.counter_service.handle_command for available commands
    :return: int, -1 on error
    makes request on port, returns received answer from port+1
    """
    global req_socket, result_socket
    if not req_socket:
        req_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if not result_socket:
        result_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        result_socket.bind(("", RES_PORT))
        result_socket.settimeout(0.5)
    # noinspection PyBroadException
    try:
        req_socket.sendto(command.encode(), ("localhost", COM_PORT))
        response = result_socket.recv(1 << 10)
        return response.decode()
    except KeyboardInterrupt as e:
        req_socket.close()
        result_socket.close()
        req_socket = None
        result_socket = None
        return ""
    except socket.timeout:
        return ERROR + ": no response from server!"
    except Exception as e:
        return ERROR + f" in send_command ({str(e)})"
