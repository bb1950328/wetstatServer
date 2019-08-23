# coding=utf-8
import time
from concurrent import futures

import RPi.GPIO as gpio

gpio.setmode(gpio.BOARD)


class LED(object):
    pin: int
    _state: bool

    def __init__(self, pin: int):
        """
        :param pin: pin number on 40p header
        """
        self.pin = pin
        self._state = False
        gpio.setup(self.pin, gpio.OUT, gpio.LOW)

    def set_state(self, state: bool) -> None:
        if self._state != state:
            self._state = state
            gpio.output(self.pin, state)

    def get_state(self) -> bool:
        return self._state

    def toggle_state(self) -> bool:
        """
        :return: new state, bool
        """
        self.set_state(not self._state)
        return self._state

    def blink(self, freq: float = 1, times: int = 10, blocking: bool = False) -> None:
        if blocking:
            ex = futures.ThreadPoolExecutor(max_workers=2)
            ex.submit(LED.blink, self, freq=freq, times=times, blocking=True)
            return
        sleep = 1 / freq / 2
        initial_state = self.get_state()
        for i in range(times):
            time.sleep(sleep)
            self.set_state(not initial_state)
            time.sleep(sleep)
            self.set_state(initial_state)
