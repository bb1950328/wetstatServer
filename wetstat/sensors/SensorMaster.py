import datetime
import numpy as np
import time

import schedule

from wetstat import logger, csvtools

"""
from wetstat.sensors.TempSensor import TempSensor

SENSORS = [
    TempSensor(1),
    TempSensor(2),
]"""

# just for debugging
from wetstat.sensors.FakeSensor import FakeSensor

SENSORS = [
    FakeSensor(1),
    FakeSensor(2),
]


class SensorMaster:
    def __init__(self):
        pass

    @staticmethod
    def get_sensor_for_info(name: str, value):
        for sensor in SENSORS:
            info = sensor.get_info()
            if name in info.keys():
                if info[name] == value:
                    return sensor
        return None

    @staticmethod
    def get_sensor_short_names():
        return [s.get_short_name() for s in SENSORS]

    @staticmethod
    def _measure_row(data: list, stoptime: datetime.datetime):
        data.append([s.measure() for s in SENSORS])
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
                                     stoptime=stoptime - datetime.timedelta(seconds=5)
                                     )
        while len(schedule.jobs):
            schedule.run_pending()
            time.sleep(1)
        means = list(np.mean(data, axis=0))
        means = [round(n) for n in means]
        csvtools.save_values(csvtools.get_data_folder(), heads, means, savedate)
        logger.log.debug("measured values" + str(means))

    @staticmethod
    def measure(freq: int = 600):
        """
        measures values forever
        :param freq: measuring frequency in seconds
        :return: None
        """

        def roundTime(dt: datetime.datetime = None, round_to: int = 60, mode=0):
            """Round a datetime object to any time lapse in seconds
            :param dt: datetime.datetime object, default now.
            :param round_to: Closest number of seconds to round to, default 1 minute.
            :param mode: -1 = to past, 0 = to nearest, 1 = to future
            """
            if dt is None: dt = datetime.datetime.now()
            seconds = (dt.replace(tzinfo=None) - dt.min).seconds
            rounding = (seconds + round_to / 2) // round_to * round_to
            delta = datetime.timedelta(0, rounding - seconds, -dt.microsecond)
            if mode < 0:
                if delta > datetime.timedelta(seconds=0):
                    delta -= datetime.timedelta(seconds=round_to)
            if mode > 0:
                if delta < datetime.timedelta(seconds=0):
                    delta += datetime.timedelta(seconds=round_to)
            res = dt + delta
            return res

        nextstop = roundTime(round_to=freq)
        while True:
            # noinspection PyBroadException
            try:
                SensorMaster.measure_now(nextstop, nextstop)
                logger.log.info("Measured and saved under label '" + nextstop.isoformat() + "'")
                nextstop += datetime.timedelta(seconds=freq)

            except Exception as e:
                logger.log.exception("Excetion occured in SensorMaster.measure")
