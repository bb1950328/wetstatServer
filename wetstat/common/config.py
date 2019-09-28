# coding=utf-8
import datetime
import io
import os.path
import sys


def get_wetstat_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


def get_datafolder() -> str:
    return os.path.join(get_wetstat_dir(), "data")


def get_staticfolder() -> str:
    return os.path.join(get_wetstat_dir(), "wetstat", "static")


def get_interpreter() -> str:
    return sys.executable


def get_date() -> datetime.datetime:
    # for development
    return datetime.datetime.now() - datetime.timedelta(days=365)  # TODO DO NOT COMMIT !!!!!!
    # noinspection PyUnreachableCode
    return datetime.datetime.now()


def get_sqlite_database() -> str:
    return os.path.join(get_wetstat_dir(), "db.sqlite3")


def on_pi() -> bool:
    cpus = ('BCM2708',
            'BCM2709',
            'BCM2835',
            'BCM2836')
    try:
        with io.open('/proc/cpuinfo') as cpuinfo:
            found = False
            info = cpuinfo.read()
            for cpu in cpus:
                if cpu in info:
                    return True
    except IOError:
        return False

    return False


MEASURING_FREQ_SECONDS = 600  # 10 minutes

ENDL = "\n" if on_pi() else "\r\n"
