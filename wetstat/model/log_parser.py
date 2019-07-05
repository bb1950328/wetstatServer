# coding=utf-8
import datetime
import os
import re
import shutil
import time
from typing import List, Optional

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

    @staticmethod
    def parse_self(inp: str):
        if not re.match(r"[\d]{4}-[\d]{2}-[\d]{2} [\d]{2}:[\d]{2}:[\d]{2},.+", inp):  # part of stacktrace
            self = TracebackLogLine()
            self.msg = inp
            return self
        self = LogLine()
        parts = inp.split(" ")
        # noinspection PyTypeChecker
        parts: List[str] = list(filter(bool, parts))
        if parts[3] == "]":
            parts.pop(3)
        if parts[4] == "]":
            parts.pop(4)
        self.time = " ".join(parts[0:2])
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


class TracebackLogLine(LogLine):
    def __init__(self) -> None:
        super().__init__()


def parse(max_lines: int = 100, level: str = LV_WARNING, filename: Optional[str] = None) -> List[LogLine]:
    if filename is None:
        filename = get_log_path()
    lines = []
    count = 0
    traceback_buffer = []
    with FileReadBackwards(filename) as f:
        for fli in f:
            ll = LogLine.parse_self(fli)
            if isinstance(ll, TracebackLogLine):
                traceback_buffer.append(ll.msg)
                continue
            if level_compare(ll.level, level):
                if traceback_buffer:
                    ll.msg += config.ENDL + config.ENDL.join(reversed(traceback_buffer))
                    traceback_buffer.clear()
                lines.append(ll)
                count += 1
                if count >= max_lines:
                    return lines
    missing = max_lines - len(lines)
    if missing > 0 and filename == get_log_path():
        lines.extend(parse(max_lines=missing, level=level, filename=get_archive_log_path()))
    return lines


def level_compare(level1: str, level2: str) -> bool:  # returns level1 >= level2
    return LEVELS.index(level1) >= LEVELS.index(level2)


def get_log_path() -> str:
    return os.path.join(config.get_wetstat_dir(), "wetstat", "wetstat.log")


def get_archive_log_path() -> str:
    return os.path.join(config.get_wetstat_dir(), "wetstat", "wetstat_archive.log")


def cleanup_log(level: str = LV_WARNING, min_days: float = 15) -> None:  # every line which is lower will be deleted
    start = time.perf_counter()
    log_file = get_log_path()
    log_out_file = log_file.replace("wetstat.log", "wetstat_new.log")
    log_archive_file = log_file.replace("wetstat.log", "wetstat_archive.log")
    threshold = datetime.datetime.now() - datetime.timedelta(days=min_days)

    lines_processed = 0
    lines_moved = 0
    last_written = 0  # 1=out, 2=arch

    with open(log_file) as log:
        with open(log_out_file, "w") as out:
            with open(log_archive_file, "a") as arch:
                for in_line in log.readlines():
                    parsed = LogLine.parse_self(in_line)
                    if isinstance(parsed, TracebackLogLine):  # line of previous traceback
                        if last_written == 1:
                            out.writelines((in_line,))
                        elif last_written == 2:
                            arch.writelines((in_line,))
                    else:  # normal line
                        lines_processed += 1
                        if parsed.get_time_dt() > threshold:  # from last xx days
                            out.writelines((in_line,))
                            last_written = 1
                        elif level_compare(parsed.level, level):  # older than xx days, but important
                            lines_moved += 1
                            arch.writelines((in_line,))
                            last_written = 2
                        else:
                            last_written = 0
    shutil.move(log_out_file, log_file)
    end = time.perf_counter()
    time_used = round(end - start, 3)
    archive_size = util.human_readable_size(os.path.getsize(log_archive_file))
    log_size = util.human_readable_size(os.path.getsize(log_file))
    logger.log.info(f"Cleaned log file in {time_used} sec. "
                    f"Processed {lines_processed} lines, moved {lines_moved} of them to the archive. "
                    f"Archive is {archive_size}, Log {log_size}")
