# coding=utf-8
import datetime
import os
import shutil
import time
from typing import List

from file_read_backwards import FileReadBackwards

from wetstat.common import config, logger
from wetstat.model import util

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
    LV_UNKNOWN,
]


class LogLine:
    def __init__(self) -> None:
        self.time = None
        self.time_dt = None
        self.thread = None
        self.level = None
        self.msg = None

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

    def get_time_dt(self) -> datetime.datetime:
        if not self.time_dt:
            try:
                self.time_dt = datetime.datetime.strptime(self.time, "%Y-%m-%dT%H:%M:%S,%f")
            except ValueError:
                self.time_dt = datetime.datetime.now()
        return self.time_dt


def parse(max_lines=100, level=LV_WARNING):
    lines = []
    count = 0
    with FileReadBackwards(get_log_path()) as f:
        for fli in f:
            ll = LogLine().parse_self(fli)
            if level_compare(ll.level, level):
                lines.append(ll)
                count += 1
                if count >= max_lines:
                    return lines
    return lines


def level_compare(level1: str, level2: str) -> bool:  # returns level1 >= level2
    return LEVELS.index(level1) >= LEVELS.index(level2)


def get_log_path() -> str:
    return os.path.join(config.get_wetstat_dir(), "wetstat", "wetstat.log")


def cleanup_log(level: str = LV_WARNING, min_days: float = 15) -> None:  # every line which is lower will be deleted
    start = time.perf_counter()
    log_file = get_log_path()
    log_out_file = log_file.replace("wetstat.log", "wetstat_new.log")
    log_archive_file = log_file.replace("wetstat.log", "wetstat_archive.log")
    threshold = datetime.datetime.now() - datetime.timedelta(days=min_days)

    lines_processed = 0
    lines_moved = 0

    with open(log_file) as log:
        with open(log_out_file, "w") as out:
            with open(log_archive_file, "a") as arch:
                for in_line in log.readlines():
                    parsed = LogLine().parse_self(in_line)
                    lines_processed += 1
                    if parsed.get_time_dt() > threshold:  # from last xx days
                        out.writelines((in_line,))
                    elif level_compare(parsed.level, level):  # older than xx days, but important
                        lines_moved += 1
                        arch.writelines((in_line,))
    shutil.move(log_out_file, log_file)
    end = time.perf_counter()
    time_used = round(end - start, 3)
    archive_size = util.human_readable_size(os.path.getsize(log_archive_file))
    log_size = util.human_readable_size(os.path.getsize(log_file))
    logger.log.info(f"Cleaned log file in {time_used} sec. "
                    f"Processed {lines_processed} lines, moved {lines_moved} of them to the archive. "
                    f"Archive is {archive_size}, Log {log_size}")
