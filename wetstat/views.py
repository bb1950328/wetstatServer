import datetime
import os
import random

from django.shortcuts import render

# Create your views here.
from wetstat import csvtools, models, logger, config
from wetstat.sensors.SensorMaster import SensorMaster


def get_static_folder():
    # TODO: make path portable
    return r"C:\Users\dev\PycharmProjects\wetstatServer\wetstat\static"


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
                "unit": sensor.get_unit(),
                "color": sensor.get_display_color(),
            }
        )
    sensors = {"array": sarr}
    context = {"sensors": sensors}
    return render(request, "wetstat/index.html", context)


def week(request):
    log_request(request)
    today = get_date()
    before7days = today - datetime.timedelta(days=7)
    data = csvtools.load_csv_for_range(csvtools.get_data_folder(), before7days, today)
    path = os.path.join(config.get_staticfolder(), "plot", "week.svg")
    models.generate_plot(data, 32, filename=path)
    context = {"plotfile": "plot/week.svg"}
    return render(request, "wetstat/week.html", context)


def month(request):
    log_request(request)
    today = get_date()
    before30days = today - datetime.timedelta(days=30)
    data = csvtools.load_csv_for_range(csvtools.get_data_folder(), before30days, today)
    path = os.path.join(config.get_staticfolder(), "plot", "month.svg")
    models.generate_plot(data, 32, filename=path, useaxis=[1, 0, 0], make_minmaxavg=[True, False, False])
    context = {"plotfile": "plot/month.svg"}
    return render(request, "wetstat/month.html", context)


def year(request):
    log_request(request)
    today = get_date()
    before365days = today - datetime.timedelta(days=365)
    data = csvtools.load_csv_for_range(csvtools.get_data_folder(), before365days, today)
    path = os.path.join(config.get_staticfolder(), "plot", "year.svg")
    models.generate_plot(data, 120, filename=path, useaxis=[1, 0, 0], make_minmaxavg=[True, False, False])
    context = {"plotfile": "plot/year.svg"}
    return render(request, "wetstat/year.html", context)


def log_request(request):
    logger.log.info("HTTP Request from " + request.get_host() + " to " + request.get_raw_uri())


def custom(request):
    log_request(request)
    return render(request, "wetstat/custom.html")
