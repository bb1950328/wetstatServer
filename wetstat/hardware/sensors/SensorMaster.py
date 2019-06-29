# coding=utf-8
import datetime
import os
import time
from typing import Optional, List

import numpy as np
import schedule

from wetstat.common import logger, config
from wetstat.hardware.sensors.BaseSensor import BaseSensor
from wetstat.hardware.sensors.FakeSensor import FakeSensor
from wetstat.hardware.sensors.OldLightSensor import OldLightSensor
from wetstat.hardware.sensors.OldTempSensor import OldTempSensor
from wetstat.hardware.sensors.TempSensor import TempSensor
from wetstat.model import csvtools

# Old Sensors
ALL_SENSORS: List[BaseSensor] = [
    OldTempSensor(2),
    OldLightSensor(),
]

USED_SENSORS: List[BaseSensor] = [
    # Used sensors on Pi
    TempSensor(1),
    TempSensor(2),
] if config.on_pi() else [
    # Used sensors on other PCs
    FakeSensor(1),
    FakeSensor(2),
]

ALL_SENSORS.extend(USED_SENSORS)

schedule.logger.setLevel(schedule.logging.ERROR)


class SensorMaster:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_sensor_for_info(name: str, value) -> Optional[BaseSensor]:
        for sensor in ALL_SENSORS:
            info = sensor.get_info()
            if name in info.keys() and info[name] == value:
                return sensor
        return None

    @staticmethod
    def get_sensor_short_names() -> List[str]:
        return [s.get_short_name() for s in USED_SENSORS]

    @staticmethod
    def _measure_row(data: list, stoptime: datetime.datetime):
        data.append([s.measure() for s in USED_SENSORS])
        if datetime.datetime.now() > stoptime:  # should stop
            return schedule.CancelJob

    @staticmethod
    def measure_now(stoptime: datetime.datetime,
                    savedate: datetime.datetime = None):
        """
        :param stoptime: timestamp on which the measurement should be finished
        :param savedate: under which date the values are saved
        :return: None
        """
        heads = SensorMaster.get_sensor_short_names()

        data = []
        schedule.every(5).seconds.do(SensorMaster._measure_row,
                                     data=data,
                                     stoptime=stoptime - datetime.timedelta(seconds=10)
                                     )
        while len(schedule.jobs):
            schedule.run_pending()
            time.sleep(1)
        means = list(np.mean(data, axis=0))
        means = [round(n, 3) for n in means]
        logger.log.debug(f"measured values {str(means)}")
        path = csvtools.save_values(config.get_datafolder(), heads, means, savedate)
        logger.log.debug(f"saved values in {os.path.basename(path)}")

    @staticmethod
    def measure(freq: int = 600):
        """
        measures values forever
        :param freq: measuring frequency in seconds
        :return: None
        """

        def round_time(dt: datetime.datetime = None, round_to: int = 60, mode=0):
            """Round a datetime object to any time lapse in seconds
            :param dt: datetime.datetime object, default now.
            :param round_to: Closest number of seconds to round to, default 1 minute.
            :param mode: -1 = to past, 0 = to nearest, 1 = to future
            """
            if dt is None:
                dt = datetime.datetime.now()
            seconds = (dt.replace(tzinfo=None) - dt.min).seconds
            rounding = (seconds + round_to / 2) // round_to * round_to
            delta = datetime.timedelta(0, rounding - seconds, -dt.microsecond)
            if mode < 0 and delta > datetime.timedelta(seconds=0):
                delta -= datetime.timedelta(seconds=round_to)
            if mode > 0 and delta < datetime.timedelta(seconds=0):
                delta += datetime.timedelta(seconds=round_to)
            res = dt + delta
            return res

        next_stop = round_time(round_to=freq, mode=1)
        while True:
            # noinspection PyBroadException
            try:
                SensorMaster.measure_now(next_stop, next_stop)
                logger.log.info("Measured and saved under label '" + next_stop.isoformat() + "'")
                next_stop += datetime.timedelta(seconds=freq)

            except Exception:
                logger.log.exception("Exception occurred in SensorMaster.measure")
