# coding=utf-8
from abc import ABC

try:
    import bme280
    import smbus2
except:
    pass

from wetstat.hardware.sensors.base_sensor import BaseSensor


class Const(object):
    BUS_NR = 1
    ADDRESS = 0x76


class BME280Base(BaseSensor, ABC):

    def __init__(self) -> None:
        try:
            self.bus = smbus2.SMBus(Const.BUS_NR)
            self.calibration = bme280.load_calibration_params(self.bus)
            self.dry_mode = False
        except (PermissionError, NameError):
            self.dry_mode = True

    def get_sample(self) -> bme280.compensated_readings:
        if self.dry_mode:
            raise ConnectionError("Can't get sample because of a permission problem while opening I2C bus")
        return bme280.sample(self.bus,
                             address=Const.ADDRESS,
                             compensation_params=self.calibration,
                             sampling=bme280.oversampling.x16)
