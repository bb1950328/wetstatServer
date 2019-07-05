# coding=utf-8
from wetstat.hardware.sensors.analog_sensor import AnalogSensor


class TempSensor(AnalogSensor):

    def __init__(self, number: int):
        if not (1 <= number <= 2):
            raise ValueError("number must be 1 or 2!!!")
        super().__init__()
        self.number = number

    def get_long_name(self) -> str:
        return f"Temperatur {self.number}"

    def get_short_name(self) -> str:
        return f"Temp{self.number}"

    def get_display_color(self) -> str:
        blue = (self.number * 50 + 150) % 255
        n = str(hex(blue))
        n = n[2:]
        if len(n) == 1:
            n = "0" + n
        return f"#3875{n}"

    def get_unit(self) -> str:
        return "°C"

    def measure(self) -> float:
        volt = self.get_volts(self.number - 1)  # limit channel
        return 35.744 * volt - 37.451
