# coding=utf-8
import os
from abc import ABC, abstractmethod

from wetstat.common import config


class BaseService(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass

    @staticmethod
    @abstractmethod
    def is_restart_after_crash() -> bool:
        pass


class DjangoServerService(BaseService):
    @staticmethod
    def is_restart_after_crash() -> bool:
        return True

    def run(self) -> None:
        pypath = os.path.join(config.get_wetstat_dir(), "manage.py")
        os.system(f"{config.get_interpreter()} {pypath} runserver 8000")
