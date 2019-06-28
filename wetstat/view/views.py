# coding=utf-8
import datetime
import os
import time

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from wetstat.common import config, logger
from wetstat.common.config import get_date
from wetstat.hardware.sensors.SensorMaster import SensorMaster, ALL_SENSORS
from wetstat.model import system_info
from wetstat.model.csvtools import get_nearest_record
from wetstat.model.custom_plot.custom_plot import CustomPlot
from wetstat.model.custom_plot.fixed_time_custom_plot import FixedTimeCustomPlot
from wetstat.model.custom_plot.request import CustomPlotRequest
from wetstat.model.custom_plot.sensor_options import CustomPlotSensorOptions
from wetstat.view.MessageContainer import MessageContainer
from wetstat.view.generatePlotThread import GeneratePlotThread

message_container = MessageContainer()


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


# noinspection PyUnusedLocal
def index(request) -> HttpResponse:
    log_request(request)

    class MockDict:
        """
        returns specified value when get() is called
        """

        def __init__(self, value: object = 0):
            self.value = value

        # noinspection PyUnusedLocal
        def get(self, *args) -> object:
            return self.value

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
    for i, name in enumerate(now.keys()):
        if name == "Time":
            continue
        y = yesterday.get(name)
        if y is not None:
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
        sensor = SensorMaster.get_sensor_for_info("short_name", name)
        unit = sensor.get_unit()
        if len(str(val)) + len(unit) > 7:  # too long to display
            val = number_maxlength(val, 7 - len(unit))
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
    sensors = {"array": sarr}
    context = {"sensors": sensors}
    return render(request, "wetstat/index.html", context)


def week(request) -> HttpResponse:
    log_request(request)
    ftcp = FixedTimeCustomPlot(7)
    so = CustomPlotSensorOptions(SensorMaster.get_sensor_for_info("short_name", "Temp1"))
    so.set_minmaxavg_interval("hour")
    ftcp.add_sensoroption(so)
    return render_generated_plot(request, ftcp, "week")


def month(request) -> HttpResponse:
    log_request(request)
    ftcp = FixedTimeCustomPlot(30)
    so = CustomPlotSensorOptions(SensorMaster.get_sensor_for_info("short_name", "Temp1"))
    so.set_minmaxavg_interval("day")
    ftcp.add_sensoroption(so)
    return render_generated_plot(request, ftcp, "month")


def year(request) -> HttpResponse:
    log_request(request)
    ftcp = FixedTimeCustomPlot(365)
    so = CustomPlotSensorOptions(SensorMaster.get_sensor_for_info("short_name", "Temp1"))
    so.set_minmaxavg_interval("week")
    ftcp.add_sensoroption(so)
    return render_generated_plot(request, ftcp, "year")


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
    if "%%finished%%" in "".join(msgs):
        save_perf(msgs)
    context = {"content": "Wrong plot id!!!" if msgs is None else "\n".join(msgs)}
    return render(request, "wetstat/dummy.html", context)


def save_perf(msgs: list):
    values = [m.split(":")[0].strip() for m in msgs]
    # print(values)
    with open(os.path.join(config.get_wetstat_dir(), "perf.csv"), "a") as f:
        f.write(";".join(values) + "\n")


def system(request):
    infos = [{"command": (" ".join(ic.get_command())), "output": mark_safe(ic.get_output())} for ic in
             system_info.ALL_INFO_CLASSES]

    context = {"infos": infos}
    return render(request, "wetstat/system.html", context)
