# coding=utf-8
import datetime
import os
import time

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from wetstat.common import config, logger
from wetstat.common.config import get_date
from wetstat.model import util, csvtools
from wetstat.model.csvtools import get_nearest_record
from wetstat.model.custom_plot.custom_plot import CustomPlot
from wetstat.model.custom_plot.fixed_time_custom_plot import FixedTimeCustomPlot
from wetstat.model.custom_plot.request import CustomPlotRequest
from wetstat.model.custom_plot.sensor_options import CustomPlotSensorOptions
from wetstat.model.util import MockDict
from wetstat.sensors.abstract.base_sensor import CompressionFunction
from wetstat.sensors.sensor_master import SensorMaster, ALL_SENSORS
from wetstat.view.generate_plot_thread import GeneratePlotThread
from wetstat.view.message_container import MessageContainer

message_container = MessageContainer()


# noinspection PyUnusedLocal
def index(request) -> HttpResponse:
    log_request(request)

    now = MockDict()
    yesterday = MockDict()
    lastmonth = MockDict()
    lastyear = MockDict()
    errors = []
    try:
        now = get_nearest_record(get_date())
    except ValueError or FileNotFoundError:
        logger.log.error("Data for HomePage not found! ")
        return show_error(request, "Es wurden keine Daten zum aktuellen Zeitpunkt gefunden.", "week.html")
    try:
        yesterday = get_nearest_record(get_date() - datetime.timedelta(days=1))
    except ValueError or FileNotFoundError as e:
        errors.append(str(e))
    try:
        lastmonth = get_nearest_record(get_date() - datetime.timedelta(days=30))
    except ValueError or FileNotFoundError as e:
        errors.append(str(e))
    try:
        lastyear = get_nearest_record(get_date() - datetime.timedelta(days=365))
    except ValueError or FileNotFoundError as e:
        errors.append(str(e))
    if errors:
        logger.log.error("Data for Home Page not found!" + str(errors))
    sarr = []
    sums_now = None
    sums_yesterday = None
    sums_lastmonth = None
    sums_lastyear = None

    def load_sums() -> None:
        global sums_now, sums_yesterday, sums_lastmonth, sums_lastyear
        if sums_now is None:
            now_date = get_date()
            oneday = datetime.timedelta(days=1)
            onemonth = datetime.timedelta(days=30)
            oneyear = datetime.timedelta(days=365)
            sums_now = csvtools.get_value_sums(end=now_date, duration=oneday)
            sums_yesterday = csvtools.get_value_sums(end=now_date - oneday, duration=oneday)
            sums_lastmonth = csvtools.get_value_sums(end=now_date - onemonth, duration=oneday)
            sums_lastyear = csvtools.get_value_sums(end=now_date - oneyear, duration=oneday)

    for i, name in enumerate(now.keys()):
        if name == "Time":
            continue
        sensor = SensorMaster.get_sensor_for_info("short_name", name)
        if sensor.get_compression_function() == CompressionFunction.SUM:
            load_sums()
            now[name] = sums_now[name]
            yesterday[name] = sums_yesterday[name]
            lastmonth[name] = sums_lastmonth[name]
            lastyear[name] = sums_lastyear[name]
        y = yesterday.get(name)
        if y:
            change = (now.get(name) / y)
        else:
            change = 1
        if change > 1.15:
            img = "arrow_up_transparent.png"
        elif change < 0.95:
            img = "arrow_down_transparent.png"
        else:
            img = "arrow_neutral_transparent.png"
        val = now.get(name)
        unit = sensor.get_unit()
        max_value_width = 12
        if len(str(val)) + len(unit) > max_value_width:  # too long to display
            val = util.number_maxlength(val, max_value_width - len(unit))
        sarr.append(
            {
                "name": sensor.get_long_name(),
                "value": val,
                "img": img,
                "before_month": lastmonth.get(name, "?"),
                "before_year": lastyear.get(name, "?"),
                "unit": unit,
                "color": sensor.get_display_color(),
            }
        )
    context = {"sensors": {"array": sarr}}
    return render(request, "wetstat/index.html", context)


def week(request) -> HttpResponse:
    return requested_fixed_time_plot(request, 7, "week", "hour", ["Temp1"])


def month(request) -> HttpResponse:
    return requested_fixed_time_plot(request, 30, "month", "day", ["Temp1"])


def year(request) -> HttpResponse:
    return requested_fixed_time_plot(request, 365, "year", "week", ["Temp1"])


def requested_fixed_time_plot(request, num_days: int, name: str, minmaxavg_interval: str,
                              sensors=None) -> HttpResponse:
    if sensors is None:
        sensors = ["Temp1"]
    log_request(request)
    ftcp = FixedTimeCustomPlot(num_days)
    for sens in sensors:
        if isinstance(sens, str):
            sens = SensorMaster.get_sensor_for_info("short_name", sens)
            so = CustomPlotSensorOptions(sens)
            so.set_minmaxavg_interval(minmaxavg_interval)
            ftcp.add_sensoroption(so)
    return render_generated_plot(request, ftcp, name)


def render_generated_plot(request, cp: CustomPlot, name: str) -> HttpResponse:
    plot_id = cp.get_plot_id()
    cp.message_container = message_container
    filename = f"{name}_plot{plot_id}.svg"
    path = os.path.join(config.get_staticfolder(), "plot", filename)
    context = {"plotfile": "/plot/" + filename,
               "plot_id": plot_id,
               "active_week": "",
               "active_month": "",
               "active_year": "",
               "active_custom": "",
               f"active_{name}": " active"}
    cp.filename = path
    cp.set_legend_mode(1)  # separate file
    thread = GeneratePlotThread(cp)
    thread.start()
    return render(request, "wetstat/show_plot.html", context)


def log_request(request):
    logger.log.info("HTTP Request from " + request.get_host() + " to " + request.get_raw_uri())


def customplot(request):
    log_request(request)
    return render(request, "wetstat/show_plot.html")


def custom_v2(request):
    def isoformat_no_seconds(dt: datetime.datetime) -> str:
        isof = dt.isoformat()
        idx = isof.rindex(":")
        return isof[:idx]

    short_names = [s.get_short_name() for s in ALL_SENSORS]
    long_names = [s.get_long_name() for s in ALL_SENSORS]
    short_names = "[\"" + "\", \"".join(short_names) + "\"]"
    long_names = "[\"" + "\", \"".join(long_names) + "\"]"
    context = {
        "start_date": isoformat_no_seconds(get_date() - datetime.timedelta(days=1)),
        "end_date": isoformat_no_seconds(get_date()),
        "short_names": mark_safe(short_names),
        "long_names": mark_safe(long_names),
    }
    return render(request, "wetstat/custom_v2.html", context=context)


def show_error(request, message: str, backlink: str):
    context = {"msg": message,
               "backlink": backlink}
    return render(request, "wetstat/error.html", context=context)


def generate_plot(request):
    log_request(request)
    cpr: CustomPlotRequest = CustomPlotRequest(request.GET)
    try:
        cpr.parse()
        return render_generated_plot(request, cpr.custom_plot, "custom")
    except ValueError as e:
        return show_error(request, str(e), "wetstat/index.html")
    except Exception:
        logger.log.exception("Exception occurred while generating plot!")


def progress(request):
    # print("get_progress")
    plot_id = request.GET.get("id")
    if "wait" in request.GET.keys():
        try:
            time.sleep(int(request.GET.get("wait")) / 1000)
        except ValueError:
            pass
    msgs = message_container.get_messages(plot_id)

    pps = message_container.get_percent_per_second(plot_id)
    if not pps:
        pps = message_container.PPS_DEFAULT_VALUE
    msgs = msgs[:]
    ppx = message_container.get_percent(plot_id)
    ppx = 0 if ppx is None else ppx
    msgs.insert(0, f"%%pps={round(pps * 100, 3)}%%")
    msgs.insert(1, f"%%ppx={round(ppx, 3)}%%")
    context = {"content": "Wrong plot id!!!" if msgs is None else "\n".join(msgs)}
    return render(request, "wetstat/dummy.html", context)
