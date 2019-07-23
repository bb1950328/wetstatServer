# coding=utf-8
import datetime
import time


def human_readable_size(size_bytes: int, round_digits: int = 3) -> str:
    sizes = {
        60: "E",
        50: "P",
        40: "T",
        30: "G",
        20: "M",
        10: "K",
    }
    prefix = ""
    for bits, prefix in sizes.items():
        s = (1 << bits)
        if size_bytes > s:
            size_bytes /= s
            break
    return f"{round(size_bytes, round_digits)}{prefix}B"


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
