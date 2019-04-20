# coding=utf-8
import os.path


def get_wetstat_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))


def get_datafolder():
    return os.path.join(get_wetstat_dir(), "data")


def get_staticfolder():
    return os.path.join(get_wetstat_dir(), "wetstat", "static")
