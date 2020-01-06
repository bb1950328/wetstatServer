# coding=utf-8
import datetime
import json
import socket
import threading
import time
from typing import Optional, List

import numpy as np
import schedule

from wetstat.common import logger
from wetstat.model import util
from wetstat.model.db import db_model
from wetstat.sensors.abstract.base_sensor import BaseSensor, CompressionFunction
from wetstat.sensors.real.digital_temp_sensor import DigitalTempSensor
from wetstat.sensors.real.fake_sensor import FakeSensor
from wetstat.sensors.real.humidity_sensor import HumiditySensor
from wetstat.sensors.real.light_sensor import LightSensor
from wetstat.sensors.real.old.old_light_sensor import OldLightSensor
from wetstat.sensors.real.old.old_temp_sensor import OldTempSensor
from wetstat.sensors.real.pressure_sensor import PressureSensor
from wetstat.sensors.real.rain_sensor import RainSensor
from wetstat.sensors.real.temp_sensor import TempSensor

OLD_SENSORS: List[BaseSensor] = [
    OldTempSensor(2),
    OldLightSensor(),
    FakeSensor(1),
    FakeSensor(2),
]

USED_SENSORS: List[BaseSensor] = [
    TempSensor(1),
    TempSensor(2),
    LightSensor(),
    DigitalTempSensor(),
    PressureSensor(),
    HumiditySensor(),
    RainSensor(),
]

ALL_SENSORS: List[BaseSensor] = [*USED_SENSORS, *OLD_SENSORS]

SUM_SENSORS = [sens for sens in ALL_SENSORS if sens.get_compression_function() == CompressionFunction.SUM]

schedule.logger.setLevel(schedule.logging.ERROR)

measuring_allowed = True
measuring_allowed_lock = threading.Lock()

last_row = {}
last_row_lock = threading.Lock()
CURRENT_VALUE_PORT = 61357


def run_current_value_provider_server() -> None:
    logger.log.info("Started current_value_provider_server")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("", CURRENT_VALUE_PORT))
        sock.listen(3)
        while True:
            com, addr = sock.accept()
            logger.log.info(f"current_value_provider_server accepted from {addr}")
            data = com.recv(1024).decode()
            if data:
                res = "{}"
                with last_row_lock:
                    res = json.dumps({sname: val for sname, val in zip(SensorMaster.get_used_sensor_short_names(), last_row)})
                com.send(res.encode())
            com.close()
    except Exception:
        logger.log.exception("Exception occurred in current_value_provider_server")
    finally:
        sock.close()


def get_current_values() -> dict:
    try:
        #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = socket.create_connection(("127.0.0.1", CURRENT_VALUE_PORT), 1)
        #sock.connect(("127.0.0.1", CURRENT_VALUE_PORT))
        sock.send("aaaa".encode())
        #sock.settimeout(1)
        return json.loads(sock.recv(4096).decode())
    except ConnectionRefusedError or ConnectionError:
        logger.log.exception("Exception in get_current_values")
        return {}


def stop_measuring() -> None:
    with measuring_allowed_lock:
        global measuring_allowed
        measuring_allowed = False


class SensorMaster(object):
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
    def get_used_sensor_short_names() -> List[str]:
        return [s.get_short_name() for s in USED_SENSORS]

    @staticmethod
    def get_all_sensor_short_names() -> List[str]:
        return [s.get_short_name() for s in ALL_SENSORS]

    @staticmethod
    def get_sum_sensor_short_names() -> List[str]:
        return [s.get_short_name() for s in SUM_SENSORS]

    @staticmethod
    def _measure_row(data: list, stoptime: datetime.datetime):
        logger.log.debug(f"SensorMaster._measure_row(len(data)={len(data)}, stoptime={stoptime.isoformat()})")
        # data.append([s.measure() for s in USED_SENSORS])
        row = []
        for s in USED_SENSORS:
            if s.get_compression_function() == CompressionFunction.SUM:
                row.append(None)  # don't call measure because it would change internal counters
            else:
                row.append(s.measure())
        data.append(row)
        with last_row_lock:
            global last_row
            last_row = row
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
        heads = SensorMaster.get_used_sensor_short_names()

        data = []
        schedule.every(5).seconds.do(SensorMaster._measure_row,
                                     data=data,
                                     stoptime=stoptime - datetime.timedelta(seconds=10)
                                     )
        while len(schedule.jobs):
            schedule.run_pending()
            with measuring_allowed_lock:
                if not measuring_allowed:
                    logger.log.info("Measuring stopped in measure_row()")
                    return
            time.sleep(1)

        values = []
        data_rows = list(zip(*data))
        for isens, sens in enumerate(USED_SENSORS):
            cf = sens.get_compression_function()
            svals = data_rows[isens]
            if cf == CompressionFunction.MINMAXAVG:
                val = np.mean(svals)
            elif cf == CompressionFunction.MIN:
                val = min(svals)
            elif cf == CompressionFunction.MAX:
                val = max(svals)
            elif cf == CompressionFunction.SUM:
                val = sens.measure()
            else:
                val = 0
            values.append(round(val, 3))

        db_model.insert_record(savedate, update_if_exists=True, **db_model.record_to_dict(values, heads))
        logger.log.debug(f"measured and saved values {str(values)}")

    @staticmethod
    def measure(freq: int = 600):
        """
        measures values forever
        :param freq: measuring frequency in seconds
        :return: None
        """

        next_stop = util.round_time(round_to=freq, mode=1)  # to future
        while True:
            # noinspection PyBroadException
            try:
                SensorMaster.measure_now(next_stop, next_stop)
                logger.log.info("Measured and saved under label '" + next_stop.isoformat() + "'")
                with measuring_allowed_lock:
                    if not measuring_allowed:
                        logger.log.info("Measuring stopped.")
                        return
                next_stop += datetime.timedelta(seconds=freq)
                now = datetime.datetime.now()
                if next_stop < now:
                    logger.log.warning(f"Time jump from {next_stop.isoformat()} to {now.isoformat()}")
                    next_stop = util.round_time(round_to=120, mode=1)

            except Exception:
                logger.log.exception("Exception occurred in SensorMaster.measure")
