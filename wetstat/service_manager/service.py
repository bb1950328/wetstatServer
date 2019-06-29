# coding=utf-8
import datetime
import os.path
import subprocess
import time
from abc import ABC, abstractmethod

import psutil

from wetstat.common import config
from wetstat.hardware.sensors.SensorMaster import SensorMaster
from wetstat.model import plot_cleanup


def kill_proc_tree(pid: int, including_parent: bool = True) -> None:
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    psutil.wait_procs(children, timeout=5)
    if including_parent:
        parent.kill()
        parent.wait(5)


class BaseService(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass

    def stop(self) -> bool:
        return False

    @staticmethod
    @abstractmethod
    def is_restart_after_crash() -> bool:
        pass


class DjangoDevServerService(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self.process = None

    @staticmethod
    def is_restart_after_crash() -> bool:
        return True

    def run(self) -> None:
        pypath = os.path.join(config.get_wetstat_dir(), "manage.py")
        self.process = subprocess.Popen(f"{config.get_interpreter()} {pypath} runserver 8000")
        print(">>>>>>>>>>>>>>>>>>before wait")
        self.process.wait()
        print(">>>>>>>>>>>>>>>>>>after wait")

    def stop(self) -> bool:
        kill_proc_tree(self.process.pid)  # SIGKILL 9, SIGINT 2, SIGTERM 15
        return True


class ApacheServerService(BaseService):
    APACHE_STATUS_OK = "Active: active (running)"

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def is_restart_after_crash() -> bool:
        return True

    def run(self) -> None:
        os.system("sudo service apache2 start")
        out = self.APACHE_STATUS_OK
        while self.APACHE_STATUS_OK in out:
            out = subprocess.getoutput("sudo service apache2 status")
            time.sleep(60)

    def stop(self) -> bool:
        os.system("sudo service apache2 stop")
        return True


class SensorService(BaseService):

    def run(self) -> None:
        sm = SensorMaster()
        sm.measure(config.MEASURING_FREQ_SECONDS)

    @staticmethod
    def is_restart_after_crash() -> bool:
        return True


class PlotCleanupService(BaseService):
    def run(self) -> None:
        while True:
            plot_cleanup.cleanup()
            now = datetime.datetime.now()
            tomorrow = datetime.datetime.today().replace(
                hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            wait = tomorrow - now
            time.sleep(wait.total_seconds())

    @staticmethod
    def is_restart_after_crash() -> bool:
        return True
