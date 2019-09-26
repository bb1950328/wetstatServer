# coding=utf-8

from wetstat.hardware.sensors.abstract.bme280_base import BME280Base


class PressureSensor(BME280Base):

    def get_long_name(self) -> str:
        return "Luftdruck"

    def get_short_name(self) -> str:
        return "Pressure"

    def get_display_color(self) -> str:
        return "#f3ff2b"

    def get_unit(self) -> str:
        return "hPa"

    def measure(self) -> float:
        return self.get_sample().pressure
