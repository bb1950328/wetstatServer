# coding=utf-8
import datetime
import os.path
import subprocess
import time
from abc import ABC, abstractmethod

import gpiozero
import psutil

from wetstat.common import config, logger
from wetstat.model import plot_cleanup, log_parser
from wetstat.sensors import counter_service, sensor_master


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
        sm = sensor_master.SensorMaster()
        sm.measure(config.MEASURING_FREQ_SECONDS)

    def stop(self) -> bool:
        sensor_master.stop_measuring()
        time.sleep(1.5)
        return True

    @staticmethod
    def is_restart_after_crash() -> bool:
        return True


class CounterService(BaseService):

    def run(self) -> None:
        server = counter_service.CounterServiceServer()
        server.run_server()

    def stop(self) -> bool:
        return False

    @staticmethod
    def is_restart_after_crash() -> bool:
        return True


class DailyService(BaseService):
    @abstractmethod
    def get_sleep_before_action(self) -> int:
        pass

    @abstractmethod
    def daily_run(self) -> None:
        pass

    def run(self) -> None:
        while True:
            time.sleep(self.get_sleep_before_action())
            self.daily_run()
            now = datetime.datetime.now()
            tomorrow = datetime.datetime.today().replace(
                hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            wait = tomorrow - now
            time.sleep(wait.total_seconds())


class PlotCleanupService(DailyService):

    def get_sleep_before_action(self) -> int:
        return 0

    def daily_run(self) -> None:
        plot_cleanup.cleanup()

    @staticmethod
    def is_restart_after_crash() -> bool:
        return True


class LogCleanupService(DailyService):

    def get_sleep_before_action(self) -> int:
        return 300

    def daily_run(self) -> None:
        log_parser.cleanup_log()

    @staticmethod
    def is_restart_after_crash() -> bool:
        return True


class ShutdownButtonService(BaseService):
    pin: int = 21  # BCM
    demo_mode = False

    def run(self) -> None:
        if config.on_pi():
            def run(command: str):
                if self.demo_mode:
                    msg = f"Would run command '{command} now, but demo_mode is on"
                    logger.log.info(msg)
                else:
                    os.system(command)

            def halt() -> None:
                run("sudo halt")

            def reboot() -> None:
                run("sudo reboot")

            button = gpiozero.Button(self.pin, pull_up=None, active_state=True, hold_time=2)
            button.when_activated = halt
            button.when_held = reboot
        while True:
            time.sleep(10)

    @staticmethod
    def is_restart_after_crash() -> bool:
        return True

class CurrentValueProviderService(BaseService):

    def run(self) -> None:
        logger.log.debug("before run_current_value_provider_server()")
        sensor_master.run_current_value_provider_server()
        logger.log.debug("after run_current_value_provider_server()")

    @staticmethod
    def is_restart_after_crash() -> bool:
        return True

