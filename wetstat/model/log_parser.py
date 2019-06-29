# coding=utf-8
import os
from typing import List

from wetstat.common import config

LV_DEBUG = "DEBUG"
LV_INFO = "INFO"
LV_WARNING = "WARNING"
LV_ERROR = "ERROR"
LV_CRITICAL = "CRITICAL"
LV_UNKNOWN = "UNKNOWN"

LEVELS = [
    LV_DEBUG,
    LV_INFO,
    LV_WARNING,
    LV_ERROR,
    LV_CRITICAL,
]


class LogLine:
    def __init__(self) -> None:
        self.time = ""
        self.thread = ""
        self.level = ""
        self.msg = ""

    def parse_self(self, inp: str):
        parts = inp.split(" ")
        # noinspection PyTypeChecker
        parts: List[str] = list(filter(bool, parts))
        if parts[3] == "]":
            parts.pop(3)
        if parts[4] == "]":
            parts.pop(4)
        self.time = "T".join(parts[0:2])
        self.thread = parts[2].strip("[] ")
        self.level = parts[3].strip("[] ")
        if self.level not in LEVELS:
            found = False
            for pl in LEVELS:
                if pl.startswith(self.level):
                    self.level = pl
                    found = True
                    break
            if not found:
                self.level = LV_UNKNOWN
        self.msg = " ".join(parts[4:]).strip()
        return self


def parse(max_lines=100, level=LV_WARNING):
    def levelfilter(line: LogLine) -> bool:
        return LEVELS.index(line.level) >= LEVELS.index(level)

    with open(os.path.join(config.get_wetstat_dir(), "wetstat", "wetstat.log")) as f:
        lines = [LogLine().parse_self(l) for l in f.readlines()]
        lines = list(filter(levelfilter, lines))
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    return lines
