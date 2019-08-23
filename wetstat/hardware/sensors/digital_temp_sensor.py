# coding=utf-8

from wetstat.hardware.sensors.bme280_base import BME280Base


class DigitalTempSensor(BME280Base):

    def get_long_name(self) -> str:
        return f"Temperatur (Digital)"

    def get_short_name(self) -> str:
        return f"DigitalTemp"

    def get_display_color(self) -> str:
        return f"#3875aa"

    def get_unit(self) -> str:
        return "°C"

    def measure(self) -> float:
        return self.get_sample().temperature
