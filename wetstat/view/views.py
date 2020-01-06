# coding=utf-8
import datetime
import os
import time
from typing import Dict, Union, Tuple, Any

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from wetstat.common import config, logger
from wetstat.common.config import get_date
from wetstat.model import util
from wetstat.model.custom_plot.custom_plot import CustomPlot
from wetstat.model.custom_plot.fixed_time_custom_plot import FixedTimeCustomPlot
from wetstat.model.custom_plot.request import CustomPlotRequest
from wetstat.model.custom_plot.sensor_options import CustomPlotSensorOptions
from wetstat.model.db import db_model
from wetstat.model.util import MockDict
from wetstat.sensors import sensor_master
from wetstat.sensors.abstract.base_sensor import CompressionFunction
from wetstat.sensors.sensor_master import SensorMaster, ALL_SENSORS
from wetstat.view.generate_plot_thread import GeneratePlotThread
from wetstat.view.message_container import MessageContainer

message_container = MessageContainer()


def load_previous_values(ndays: int) -> Tuple[datetime.datetime, Dict[str, float]]:
    delta = datetime.timedelta(days=ndays)
    oneday = datetime.timedelta(days=1)
    now_date = config.get_date()
    try:
        value_record = db_model.find_nearest_record(now_date - delta)
        sum_record = db_model.get_value_sums(columns=SensorMaster.get_sum_sensor_short_names(),
                                             end=now_date - delta,
                                             duration=oneday)
    except ValueError or FileNotFoundError:
        logger.log.exception(f"Error while loading data for {ndays} before!")
        return datetime.datetime.fromtimestamp(0), MockDict()
    ret_record = {}
    record_timestamp = None
    for short_name in value_record.keys():
        if short_name == "Time":
            record_timestamp = value_record[short_name]
            continue
        sensor = SensorMaster.get_sensor_for_info("short_name", short_name)
        if sensor.get_compression_function() == CompressionFunction.SUM:
            rec = sum_record
        else:
            rec = value_record
        ret_record[short_name] = rec[short_name]
    return record_timestamp, ret_record


def index(request) -> HttpResponse:
    log_request(request)

    ts_0, today = datetime.datetime.now(), sensor_master.get_current_values()
    if not today:
        ts_0, today = load_previous_values(0)
    ts_1, yesterday = load_previous_values(1)
    ts_30, lastmonth = load_previous_values(30)
    ts_365, lastyear = load_previous_values(365)

    if isinstance(today, MockDict):
        return show_error(request, "Es wurden keine Daten zum aktuellen Zeitpunkt gefunden.", "week.html")
    sarr = []
    for i, name in enumerate(today.keys()):
        if name == "Time":
            continue
        sensor = SensorMaster.get_sensor_for_info("short_name", name)

        unit = sensor.get_unit()
        v_today = today.get(name)
        v_yesterday = yesterday.get(name)
        v_lastmonth = lastmonth.get(name, "?")
        v_lastyear = lastyear.get(name, "?")
        if v_today is None:
            continue
        if v_yesterday is None:
            v_yesterday = 0
        if v_lastmonth is None:
            v_lastmonth = "?"
        if v_lastyear is None:
            v_lastyear = "?"
        sarr.append(
            {
                "name": sensor.get_long_name(),
                "value": limit_number_length(v_today, unit),
                "img": select_trend_img(v_today, v_yesterday),
                "before_month": v_lastmonth,
                "before_year": v_lastyear,
                "unit": unit,
                "color": sensor.get_display_color(),
            }
        )
    context = {
        "sensors": {"array": sarr},
        "record_dates": f"{ts_0}, {ts_1}, {ts_30}, {ts_365}",
        **get_base_context("index"),
    }
    return render(request, "wetstat/index.html", context)


def limit_number_length(val: float, unit: str, maxlength: int = 10) -> Union[str, float]:
    if len(str(val)) + len(unit) > maxlength:  # too long to display
        val = util.number_maxlength(val, maxlength - len(unit))
    return val


def select_trend_img(today: float, yesterday: float, threshold: float = 0.15) -> str:
    if yesterday:
        change = (today / yesterday)
    else:
        change = 1

    if change > 1 + threshold:
        return "arrow_up_transparent.png"
    elif change < 1 - threshold:
        return "arrow_down_transparent.png"
    else:
        return "arrow_neutral_transparent.png"


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
    context = {
        "plotfile": "/plot/" + filename,
        "plot_id": plot_id,
        "active_week": "",
        "active_month": "",
        "active_year": "",
        "active_custom": "",
        f"active_{name}": " active",
        **get_base_context(name),
    }
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
        **get_base_context("custom_v2"),
    }
    return render(request, "wetstat/custom_v2.html", context=context)


def show_error(request, message: str, backlink: str):
    context = {
        "msg": message,
        "backlink": backlink,
        **get_base_context(""),
    }
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


def get_base_context(active_nav_id: str) -> Dict[str, Any]:
    return {
        "active_nav_id": active_nav_id
    }
