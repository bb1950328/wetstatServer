# coding=utf-8
import os.path
import subprocess
from abc import ABC, abstractmethod

import psutil

from wetstat.common import config


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


class DjangoServerService(BaseService):
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
