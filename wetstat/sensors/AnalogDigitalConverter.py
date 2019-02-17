import time

from wetstat import logger

try:
    import spidev
    ON_PI = True
except ModuleNotFoundError:  # not on raspberry pi
    ON_PI = False


class AnalogDigitalConverter:
    def __init__(self):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 1)

    def read_channel(self, channel, timeout=1):
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
                value = ((answer[1] * 256) + answer[2]) * 0.00322
        return value
