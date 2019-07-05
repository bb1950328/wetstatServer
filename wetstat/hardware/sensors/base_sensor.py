# coding=utf-8
from abc import ABC, abstractmethod
from enum import Enum


class BaseSensor(ABC):
    class CompressionFunction(Enum):
        MINMAXAVG = "minmaxavg"
        SUM = "sum"
        MIN = "min"
        MAX = "max"

    def get_info(self) -> dict:
        try:
            return {"long_name": self.get_long_name(),
                    "short_name": self.get_short_name(),
                    "color": self.get_display_color(),
                    "unit": self.get_unit()}
        except NameError:
            raise NotImplementedError("child class hasn't defined one of the info methods correctly!")

    @abstractmethod
    def get_long_name(self) -> str:
        pass

    @abstractmethod
    def get_short_name(self) -> str:
        pass

    @abstractmethod
    def get_display_color(self) -> str:
        pass

    @abstractmethod
    def get_unit(self) -> str:
        pass

    def get_compression_function(self) -> CompressionFunction:
        return self.CompressionFunction.MINMAXAVG

    @abstractmethod
    def measure(self) -> float:
        pass
