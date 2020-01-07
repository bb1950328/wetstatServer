# coding=utf-8
import logging
import os

from wetstat.model import util

LEVEL = logging.DEBUG

log_format = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s [in file %(module)s ]"
logFormatter = logging.Formatter(log_format)
logging.basicConfig(level=LEVEL, filemode="a")
log = logging.getLogger("wetstat")

if util.is_apache_process():
    fname = "/var/www/wetstat.log"
else:
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
