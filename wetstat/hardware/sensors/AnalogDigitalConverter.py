# coding=utf-8
import time
from typing import Optional

from wetstat.common import logger

try:
    import spidev

    ON_PI = True
except ModuleNotFoundError:  # not on raspberry pi
    ON_PI = False


class AnalogDigitalConverter:
    def __init__(self, volt_reference: float = 3.3, num_bits: int = 10) -> None:
        self.spi = spidev.SpiDev()
        self.spi.open(0, 1)
        self.spi.max_speed_hz = 7800000
        self.volts_per_bit = volt_reference / pow(2, num_bits)

    def read_channel_bits(self, channel: int, timeout: float = 1) -> Optional[int]:
        if not ON_PI:
            logger.log.warning("Someone tried to read values from ADC but not on Raspberry Pi")
            return 0
        if not (0 <= channel <= 7):
            raise ValueError("channel is not between 0 and 7")
        start_time = time.perf_counter()
        command = [1, 128 + channel * 16, 8]
        answer = self.spi.xfer(command)
        value = None
        while (value is None) and ((time.perf_counter() - start_time) < timeout):
            if 0 <= answer[1] <= 3:
                return (answer[1] * 256) + answer[2]
        return None

    def read_channel_volt(self, channel: int, timeout: float = 1) -> float:
        return self.read_channel_bits(channel, timeout) * self.volts_per_bit
