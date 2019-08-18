# coding=utf-8
import logging
import os

LEVEL = logging.DEBUG

log_format = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s [in file %(module)s ]"
logFormatter = logging.Formatter(log_format)
logging.basicConfig(level=LEVEL, filemode="a")
log = logging.getLogger("wetstat")

fname = os.path.join(
    os.path.realpath(os.path.dirname(__file__)),
    "../wetstat.log")

fileHandler = logging.FileHandler(fname)
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(LEVEL)
log.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
consoleHandler.setLevel(LEVEL)
log.addHandler(consoleHandler)
