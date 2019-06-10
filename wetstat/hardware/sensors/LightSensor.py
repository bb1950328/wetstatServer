# coding=utf-8
from wetstat.hardware.sensors.AnalogSensor import AnalogSensor


class LightSensor(AnalogSensor):
    def __init__(self, channel: int = 2) -> None:
        super().__init__()
        self.channel = channel

    def get_long_name(self) -> str:
        return "Licht"

    def get_short_name(self) -> str:
        return "Light"

    def get_display_color(self) -> str:
        return "#f9d607"

    def get_unit(self) -> str:
        return "Lux"

    def measure(self) -> float:
        return 9.5785 * self.get_bits(self.channel) - 2025.8
