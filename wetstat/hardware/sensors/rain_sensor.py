# coding=utf-8
from wetstat.hardware.sensors.base_sensor import BaseSensor, CompressionFunction


class RainSensor(BaseSensor):
    def get_compression_function(self) -> CompressionFunction:
        return CompressionFunction.SUM

    def get_display_color(self) -> str:
        return "#0000ff"

    def get_unit(self) -> str:
        return "mm"

    def get_long_name(self) -> str:
        return "Niederschlag"

    def get_short_name(self) -> str:
        return "Rain"

    def measure(self) -> float:
        pass
        # TODO implement
        #  - system-global counter
        #  - service to increase counter for every pulse
        #  - this method is called once before the values are written
        #  - this method returns the counter value and resets it
