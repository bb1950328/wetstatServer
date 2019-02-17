import datetime
import random

from django.shortcuts import render

# Create your views here.
from wetstat import csvtools, models, logger
from wetstat.sensors.SensorMaster import SensorMaster


def get_date() -> datetime.datetime:
    # for development
    return datetime.datetime.now() - datetime.timedelta(days=365)
    # noinspection PyUnreachableCode
    return datetime.datetime.now()


def number_maxlength(inp: float, maxlen: int) -> str:
    si = str(inp)
    if len(si) < maxlen:
        return si
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
        print("new exponent= " + str(new_exp), new_exp)
    return si


def index(request):
    log_request(request)
    now = models.get_nearest_record(get_date())
    yesterday = models.get_nearest_record(get_date() - datetime.timedelta(days=1))
    lastmonth = models.get_nearest_record(get_date() - datetime.timedelta(days=30))
    lastyear = models.get_nearest_record(get_date() - datetime.timedelta(days=365))

    sarr = []
    for i, name in enumerate(now.keys()):
        if name == "Time":
            continue
        change = (now.get(name) / yesterday.get(name)) - 1
        if change > 1.15:
            img = "arrow_up_transparent.png"
        elif change < 0.95:
            img = "arrow_down_transparent.png"
        else:
            img = "arrow_neutral_transparent.png"
        val = now.get(name)
        if len(str(val)) > 7:  # too long to display
            val = number_maxlength(val, 7)
        sensor = SensorMaster.get_sensor_for_info("short_name", name)
        sarr.append(
            {
                "name": sensor.get_long_name(),
                "value": val,
                "img": img,
                "before_month": lastmonth.get(name, "?"),
                "before_year": lastyear.get(name, "?"),
                "unit": sensor.get_unit()
            }
        )
    sensors = {"array": sarr}
    context = {"sensors": sensors}
    return render(request, "wetstat/index.html", context)


def week(request):
    log_request(request)
    return render(request, "wetstat/week.html")


def month(request):
    log_request(request)
    return render(request, "wetstat/month.html")


def year(request):
    log_request(request)
    return render(request, "wetstat/year.html")


def log_request(request):
    logger.log.info("HTTP Request from " + request.get_host() + " to " + request.get_raw_uri())
