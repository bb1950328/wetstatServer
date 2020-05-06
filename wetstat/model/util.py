# coding=utf-8
import datetime
import re
import time
import subprocess
from typing import Union, Optional, List

import psutil

IP_ADDRESS_PATTERN = r"\d\d\d\.\d\d\d\.\d\d\d\.\d\d\d"

def human_readable_size(size_bytes: Union[int, float], round_digits: int = 3, unit: str = "B") -> str:
    sizes = {
        60: "E",
        50: "P",
        40: "T",
        30: "G",
        20: "M",
        10: "K",
    }
    prefix = ""
    for bits, pr in sizes.items():
        s = (1 << bits)
        if size_bytes > s:
            size_bytes /= s
            prefix = pr
            break
    return f"{round(size_bytes, round_digits)}{prefix}{unit}"


def round_time(dt: datetime.datetime = None, round_to: int = 60, mode=0):
    """Round a datetime object to any time lapse in seconds
    :param dt: datetime.datetime object, default now.
    :param round_to: Closest number of seconds to round to, default 1 minute.
    :param mode: -1 = to past, 0 = to nearest, 1 = to future
    """
    if dt is None:
        dt = datetime.datetime.now()
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds + round_to / 2) // round_to * round_to
    delta = datetime.timedelta(0, rounding - seconds, -dt.microsecond)
    if mode < 0 and delta > datetime.timedelta(seconds=0):
        delta -= datetime.timedelta(seconds=round_to)
    if mode > 0 and delta < datetime.timedelta(seconds=0):
        delta += datetime.timedelta(seconds=round_to)
    res = dt + delta
    return res


def swap_bytes(inp: int):
    if inp < 0 or inp > 0xffff:
        raise ValueError("parameter is negative or bigger than 2 bytes!!!")
    return inp >> 8 | (inp & 0xff) << 8


def get_time_ms() -> float:
    return time.perf_counter_ns() / 1000


def number_maxlength(inp: float, maxlen: int) -> str:
    si = str(inp)
    si2 = str(int(inp))
    if len(si) < maxlen:
        return si
    elif len(si2) <= maxlen:
        return si2
    mult = 0
    while "e" not in si:
        inp *= 10
        si = str(inp)
        mult += 1
    if len(si) > maxlen:
        a, b = si.split("e")
        vz = b[0]  # + or -
        new_exp = int(b[1:])
        if vz == "-":
            new_exp *= -1
        new_exp -= mult
        to_del = len(si) - maxlen - 1
        if new_exp > 0:
            to_del -= 1
        a = a[:-to_del]
        si = a + "e" + str(new_exp)
    return si


class MockDict(dict):
    """
    returns specified value when get() is called
    """

    def __init__(self, value: object = 0):
        self.value = value

    # noinspection PyUnusedLocal
    def get(self, key, default=None) -> object:
        if default:
            return default
        return self.value


def is_valid_sql_name(to_test: str) -> bool:
    return bool(re.match(r"\A[\w]+\Z", to_test))


def validate_start_end(start: datetime.datetime, end: datetime.datetime) -> None:
    if start is None:
        raise ValueError("start must not be None!!!")
    elif end is None:
        raise ValueError("end must not be None!!!")
    if isinstance(start, datetime.date):
        start = date_to_datetime(start)
    if isinstance(end, datetime.date):
        end = date_to_datetime(end)
    if start > end:
        raise ValueError("end must be after start!!!")


def date_to_datetime(date: datetime.date, take_max_time=False) -> datetime.datetime:
    if isinstance(date, datetime.datetime):
        return date  # already a datetime, nothing to do
    min_or_max = datetime.datetime.max.time() if take_max_time else datetime.datetime.min.time()
    return datetime.datetime.combine(date, min_or_max)


def calculate_missing_start_end_duration(start: Optional[datetime.datetime],
                                         end: Optional[datetime.datetime],
                                         duration: Optional[datetime.timedelta]):
    if not start and end and duration:
        start = end - duration
    elif start and not end and duration:
        end = start + duration
    elif start and end and not duration:
        duration = end - start
    else:
        raise ValueError("At least two of the three parameters must not be None!!")
    return start, end, duration


def get_parent_process_names() -> List[str]:
    proc = psutil.Process()
    names = []
    while proc:
        names.append(proc.name())
        proc = proc.parent()
    return names


def is_apache_process() -> bool:
    return "apache2" in get_parent_process_names()


def make_color_lighter(old: str) -> str:
    old = old[1:]  # cut the '#'
    parts = [old[0:2], old[2:4], old[4:6]]
    parts = [hex(int((int(v, 16) + 255) / 2))[2:] for v in parts]
    return f"#{''.join(parts)}"

def get_my_ip() -> str:
    status, outp = subprocess.getstatusoutput("ipconfig")
    if status == 0:
        return re.findall(IP_ADDRESS_PATTERN, outp)[0]
    else:
        return subprocess.getoutput("hostname -I").strip()
