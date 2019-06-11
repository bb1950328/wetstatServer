# coding=utf-8
import datetime
import os.path


def get_wetstat_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


def get_datafolder():
    return os.path.join(get_wetstat_dir(), "data")


def get_staticfolder():
    return os.path.join(get_wetstat_dir(), "wetstat", "static")


def get_date() -> datetime.datetime:
    # for development
    return datetime.datetime.now() - datetime.timedelta(days=365)
    # noinspection PyUnreachableCode
    return datetime.datetime.now()
