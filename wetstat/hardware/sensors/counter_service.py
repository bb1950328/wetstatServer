# coding=utf-8
import random
import socket
import threading
import time
from concurrent import futures
from typing import Dict

from wetstat.common import config

if config.on_pi():
    import RPi.GPIO as gpio

    gpio.setmode(gpio.BOARD)


class CounterManager(object):
    def __init__(self) -> None:
        self.list_lock = threading.Lock()
        self.counters: Dict[int, int] = {}
        self.counter_locks: Dict[int, threading.Lock] = {}

    def add_counter(self, pin) -> None:
        with self.list_lock:
            self.counters[pin] = 0
            self.counter_locks[pin] = threading.Lock()

    def remove_counter(self, pin: int) -> None:
        with self.list_lock:
            del self.counters[pin]
            del self.counter_locks[pin]

    def count(self, pin: int, amount=1) -> None:
        with self.counter_locks[pin]:
            self.counters[pin] += amount

    def get_and_reset(self, pin: int) -> int:
        return self.get(pin, reset=True)

    def get(self, pin: int, reset: bool = False) -> int:
        with self.counter_locks[pin]:
            value = self.counters[pin]
            if reset:
                self.counters[pin] = 0
        return value


counters = CounterManager()


def start(pin: int, mode=gpio.RISING) -> None:
    if not config.on_pi():
        return start_fake(pin)
    counters.add_counter(pin)
    gpio.setup(pin, gpio.IN)
    gpio.add_event_detect(pin, mode)
    gpio.add_event_callback(pin, build_detector(pin))


def start_fake(pin: int) -> None:
    counters.add_counter(pin)
    func = build_detector(pin)

    def fake_callback() -> None:
        while True:
            time.sleep(random.randint(100, 1000))
            func()

    ex = futures.ThreadPoolExecutor()
    ex.submit(fake_callback)


def build_detector(pin: int) -> callable:
    def pulse_detected() -> None:
        counters.count(pin)

    return pulse_detected


def server(port: int) -> None:
    """
    :param port: port number, should be between 1 and 65536
    :return: None
    listens on UDP port and sends back on UDP port+1
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind(("", port))
        while True:
            data, (ip, port) = s.recvfrom(1 << 10)
            data = data.decode(errors="replace")
            res = handle_command(data)

            s.sendto(res.encode(), (ip, port + 1))

    finally:
        s.close()


def handle_command(data: str) -> str:
    # noinspection PyBroadException
    try:
        res = "OK"
        pin = int(data.split(" ")[1])

        if data == "get":
            res = str(counters.get_and_reset(pin)).encode()
        elif data.startswith("stop"):
            gpio.remove_event_detect(pin)
            counters.remove_counter(pin)
        elif data.startswith("start"):
            start(pin)

        return res
    except Exception:
        return "ERROR"


req_socket = None
result_socket = None


def send_command(port: int, command: str) -> int:
    """
    :param command: look in wetstat.hardware.sensors.counter_service.handle_command for available commands
    :param port: port number, should be between 1 and 65536
    :return: int, -1 on error
    makes request on port, returns received answer from port+1
    """
    global req_socket, result_socket
    if not req_socket:
        req_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if not result_socket:
        result_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        result_socket.bind(("", port + 1))
    # noinspection PyBroadException
    try:
        req_socket.sendto(command.encode(), ("localhost", port))
        response = result_socket.recv(1 << 10)
        return int(response.decode())
    except Exception:
        return -1
