# coding=utf-8
import datetime
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
    # return datetime.datetime.now() - datetime.timedelta(days=365)
    # noinspection PyUnreachableCode
    return datetime.datetime.now()


def get_database() -> str:
    return os.path.join(get_wetstat_dir(), "db.sqlite3")


def on_pi() -> bool:
    return sys.platform != "win32"


MEASURING_FREQ_SECONDS = 600  # 10 minutes
