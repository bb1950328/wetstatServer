# coding=utf-8
from abc import ABC

import bme280
import smbus2

from wetstat.hardware.sensors.base_sensor import BaseSensor


class Const:
    BUS_NR = 1
    ADDRESS = 0x76


class BME280Base(BaseSensor, ABC):

    def __init__(self) -> None:
        self.bus = smbus2.SMBus(Const.BUS_NR)
        bme280.DEFAULT_PORT = Const.ADDRESS
        self.calibration = bme280.load_calibration_params(self.bus)

    def get_sample(self) -> bme280.compensated_readings:
        return bme280.sample(self.bus, compensation_params=self.calibration, sampling=bme280.oversampling.x16)
