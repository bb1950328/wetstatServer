# coding=utf-8
import datetime
import os
import random
import threading
import time
from typing import Dict, List, Optional

from django.shortcuts import render
from django.utils.safestring import mark_safe

from wetstat import csvtools, models, logger, config
from wetstat.forms import CustomPlotForm
from wetstat.sensors.SensorMaster import SensorMaster, ALL_SENSORS


# Create your views here.
class MessageContainer:
    def __init__(self):
        self._messages: Dict[str, List[str]] = {}
        self.messages_lock = threading.Lock()
        self.messages_lock_reversed = threading.Lock()

    def add_message(self, plot_id: str, messge: str) -> None:
        with self.messages_lock:
            if plot_id not in self._messages.keys():
                self._messages[plot_id] = []
            self._messages[plot_id].append(messge)

    def get_messages(self, plot_id: str) -> Optional[List[str]]:
        with self.messages_lock:
            try:
                return self._messages[plot_id]
            except KeyError:
                return None


message_container = MessageContainer()


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


# noinspection PyUnusedLocal
def index(request):
    log_request(request)

    class MockDict:
        """
        returns specified value when get() is called
        """

        def __init__(self, value=0):
            self.value = value

        # noinspection PyUnusedLocal
        def get(self, *args):
            return self.value

    now = MockDict()
    yesterday = MockDict()
    lastmonth = MockDict()
    lastyear = MockDict()
    errors = []
    try:
        now = models.get_nearest_record(get_date())
    except ValueError or FileNotFoundError:
        logger.log.error("Data for HomePage not found! ")
        return show_error(request, "Es wurden keine Daten zum aktuellen Zeitpunkt gefunden.", "week.html")
    try:
        yesterday = models.get_nearest_record(get_date() - datetime.timedelta(days=1))
    except ValueError or FileNotFoundError as e:
        errors.append(str(e))
    try:
        lastmonth = models.get_nearest_record(get_date() - datetime.timedelta(days=30))
    except ValueError or FileNotFoundError as e:
        errors.append(str(e))
    try:
        lastyear = models.get_nearest_record(get_date() - datetime.timedelta(days=365))
    except ValueError or FileNotFoundError as e:
        errors.append(str(e))
    if errors:
        logger.log.error("Data for Home Page not found!" + str(errors))
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
    # If this is a POST request then process the Form data
    if request.method == 'POST':
        form = CustomPlotForm(request.POST)
        if form.is_valid():
            # redirect to a new URL:
            start = form.clean_start_date()
            end = form.clean_end_date()
            start_iso = start.isoformat()
            end_iso = end.isoformat()
            start_fn = start_iso
            end_fn = end_iso
            start_fn = start_fn.replace(":", "_")
            end_fn = end_fn.replace(":", "_")
            start_view = start.strftime("%d.%m.%Y %H:%M")
            end_view = end.strftime("%d.%m.%Y %H:%M")
            try:
                data = csvtools.load_csv_for_range(csvtools.get_data_folder(), start, end)
            except Exception:
                logger.log.exception("Could not load data for custom plot!")
                return show_error(request, "Daten konnten nicht geladen werden!", "custom.html")
            filename = "from" + start_fn + "to" + end_fn + ".svg"
            logger.log.info("generating custom plot from " + start_iso + " to " + end_iso + " -> " + filename)
            try:
                path = os.path.join(config.get_staticfolder(), "plot", filename)
                models.generate_plot(data, 120, filename=path, useaxis=[1, 0, 0],
                                     make_minmaxavg=[form.clean_use_minmaxavg(), False, False])
            except Exception:
                logger.log.exception("Exception occurred while generating Graph")
                return show_error(request, "Graph konnte nicht erstellt werden!", "custom.html")

            context = {"plotfile": "plot/" + filename,
                       "start": start_view,
                       "end": end_view
                       }
            return render(request, "wetstat/customplot.html", context=context)

    # If this is a GET (or any other method) create the default form.
    else:
        default_start_date = datetime.datetime.now() - datetime.timedelta(days=1)
        form = CustomPlotForm(initial={'start_date': default_start_date})

    context = {
        'form': form,
    }
    return render(request, "wetstat/custom.html", context)


def customplot(request):
    log_request(request)
    return render(request, "wetstat/customplot.html")


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
    class GeneratePlotThread(threading.Thread):
        def __init__(self, custom_plot_request: models.CustomPlotRequest):
            super().__init__()
            self.cpr = custom_plot_request

        def run(self) -> None:
            self.cpr.custom_plot.create_plots()

    log_request(request)
    print(request.GET)
    cpr: models.CustomPlotRequest = models.CustomPlotRequest(request.GET)
    try:
        cpr.parse()
        cpr.custom_plot.plot_id = hex(random.randint(0x1000000000000, 0xfffffffffffff))[2:]
        cpr.custom_plot.message_container = message_container
        filename = "plot{}.svg".format(cpr.custom_plot.plot_id)
        path = os.path.join(config.get_staticfolder(), "plot", filename)
        context = {"plotfile": "/plot/" + filename,
                   "plot_id": cpr.custom_plot.plot_id,
                   }
        cpr.custom_plot.filename = path
        cpr.custom_plot.set_legend_mode(1)  # separate file
        thread = GeneratePlotThread(cpr)
        thread.start()
        # cpr.custom_plot.create_plots()
        return render(request, "wetstat/customplot.html", context=context)
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
    context = {"content": "Wrong plot id!!!" if msgs is None else "\n".join(msgs)}
    return render(request, "wetstat/dummy.html", context)


def system(request):
    context = {}
    return render(request, "wetstat/system.html", context)
