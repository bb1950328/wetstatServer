# coding=utf-8
from abc import ABC

from wetstat.sensors.abstract.analog_digital_converter import AnalogDigitalConverter
from wetstat.sensors.abstract.base_sensor import BaseSensor


class AnalogSensor(BaseSensor, ABC):

    def __init__(self) -> None:
        self.adc = None

    def set_adc(self, adc: AnalogDigitalConverter) -> None:
        self.adc = adc

    def get_adc(self) -> AnalogDigitalConverter:
        if self.adc is None:
            self.adc = AnalogDigitalConverter()
        return self.adc

    def get_bits(self, channel: int) -> int:
        return self.get_adc().read_channel_bits(channel)

    def get_volts(self, channel: int) -> float:
        return self.get_adc().read_channel_volt(channel)
