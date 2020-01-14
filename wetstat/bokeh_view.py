# coding=utf-8
import datetime
import pprint
from typing import Optional, List

import numpy as np
from bokeh.client import pull_session
from bokeh.embed import server_session
from bokeh.layouts import column, row
from bokeh.models import DataRange1d, Select, Toggle, ColumnDataSource, LinearAxis, Column, Div
from bokeh.models.widgets import DatePicker
from bokeh.plotting import figure, Figure
from bokeh.server.server import Server
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from wetstat.model import util
from wetstat.model.db import db_model
from wetstat.sensors import sensor_master
from wetstat.view import views

MAX_SUBPLOTS = 3

ALL_SHORT_NAMES = sensor_master.SensorMaster.get_used_sensor_short_names()

URL = "/wetstat_bokeh"
PORT = 5006
DEFAULT_ACTIVE_SENSORS = ["DigitalTemp"]


def bkapp_view(request: WSGIRequest) -> HttpResponse:
    with pull_session(url=f"http://localhost:{PORT}{URL}") as session:
        # update or customize that session
        session.document.roots[0].children[1].title.text = "Special Sliders For A Specific User!"

        # generate a script to load the customized session
        script = server_session(session_id=session.id, url=f'http://localhost:{PORT}{URL}')

        # use the script in the rendered page
        context = {
            "script": mark_safe(script),
            **views.get_base_context("bokeh")
        }
        return render(request, "wetstat/bokeh_embed.html", context)


class WetstatPlot(object):
    def __init__(self, nr, app) -> None:
        self._sensor_list_a: List[str] = []
        self._sensor_list_b: List[str] = []
        self._renderers_a = {}
        self._renderers_b = {}
        self._unit_a = None
        self._unit_b = None
        self.nr = nr
        self.app = app
        self.plot: Optional[Figure] = None
        self.y_axis_2 = None
        self.create_plot()

    @property
    def unit_a(self) -> str:
        return self._unit_a

    @unit_a.setter
    def unit_a(self, new) -> None:
        if self._unit_a != new:
            print(f"Unit {self.nr}a is {new} now. (was {self._unit_a})")
        self._unit_a = new
        self.plot.yaxis.axis_label = self._generate_axis_label(self._unit_a)

    @property
    def unit_b(self) -> str:
        return self._unit_b

    @unit_b.setter
    def unit_b(self, new) -> None:
        if self._unit_b != new:
            print(f"Unit {self.nr}b is {new} now. (was {self._unit_b})")
        self._unit_b = new
        if new is None:
            self._remove_2nd_axis()
        else:
            self._add_2nd_y_axis()

    @property
    def sensor_list_a(self) -> List[str]:
        return self._sensor_list_a

    @property
    def sensor_list_b(self) -> List[str]:
        return self._sensor_list_b

    def refresh_lines(self) -> None:
        print(f"Refreshing lines for nr={self.nr}")
        in_list = {*self.sensor_list_a, *self.sensor_list_b}
        in_renderer = {*self._renderers_a.keys(), *self._renderers_b.keys()}
        all_sensors = {*in_list, *in_renderer}
        for sn in all_sensors:
            sens = sensor_master.SensorMaster.get_sensor_for_info("short_name", sn)
            if sn not in in_list:
                if sn in self._renderers_a.keys():
                    self._renderers_a[sn].visible = False
                    print(f"{sn} not in {self.nr}a anymore.")
                elif sn in self._renderers_b.keys():
                    self._renderers_b[sn].visible = False
                    print(f"{sn} not in {self.nr}b anymore.")
            else:
                moved = False
                if sn in self.sensor_list_a and sn in self._renderers_b and self._renderers_b[sn].visible:
                    self._renderers_b[sn].visible = False
                    if sn in self._renderers_a:
                        self._renderers_a[sn].visible = True
                        self.unit_a = sens.get_unit()
                    else:
                        moved = True
                    print(f"{sn} moved from {self.nr}b to {self.nr}a (but stayed in same plot)")
                if sn in self.sensor_list_b and sn in self._renderers_a and self._renderers_a[sn].visible:
                    self._renderers_a[sn].visible = False
                    if sn in self._renderers_b:
                        self._renderers_b[sn].visible = True
                        self.unit_b = sens.get_unit()
                    else:
                        moved = True
                    print(f"{sn} moved from {self.nr}a to {self.nr}b (but stayed in same plot)")

                if sn not in in_renderer or moved:
                    if sn in self.app.data.columns:
                        rlist = self._renderers_a if sn in self.sensor_list_a else self._renderers_b
                        is_a = rlist == self._renderers_a
                        rlist[sn] = self.plot.line("Time", sn, source=self.app.cds,
                                                   color=sens.get_display_color(),
                                                   # legend_label=sens.get_long_name(),
                                                   y_range_name="default" if is_a else "b",
                                                   )
                        print(f"created new line {sn} on {self.nr}{'a' if is_a else 'b'}")
                        if is_a:
                            self.unit_a = sens.get_unit()
                        else:
                            self.unit_b = sens.get_unit()
                    else:
                        print(f"no data found for {sn}!!!")
                else:
                    if sn in self.sensor_list_a:
                        if sn in self._renderers_a:
                            self._renderers_a[sn].visible = True
                            self.unit_a = sens.get_unit()
                            print(f"{sn} appeared again on {self.nr}a")
                    else:
                        if sn in self._renderers_b:
                            self._renderers_b[sn].visible = True
                            self.unit_b = sens.get_unit()
                            print(f"{sn} appeared again on {self.nr}b")
        if not self.sensor_list_a:
            self.unit_a = None
        if not self.sensor_list_b:
            self.unit_b = None
        self.plot.visible = bool(self.unit_a or self.unit_b)
        # TODO rescale axes a and b to visible glyphs

    @staticmethod
    def _generate_axis_label(unit: str) -> str:
        try:
            return f"{sensor_master.UNIT_NAMES[unit]} [{unit}]"
        except KeyError:
            return f"[{unit}]"

    def _add_2nd_y_axis(self) -> None:
        self.y_axis_2.visible = True
        self.y_axis_2.axis_label = self._generate_axis_label(self._unit_b)

    def _remove_2nd_axis(self) -> None:
        if self.y_axis_2 is not None:
            self.y_axis_2.visible = False

    def create_plot(self) -> None:
        self.plot = figure(
            x_axis_type="datetime",
            x_axis_label='Zeit',
            tools=["xpan", "xwheel_zoom", "hover", "crosshair", "reset", "save"],
            title=f"Graph {self.nr}",
        )
        self.plot.y_range.name = "a"
        self.plot.x_range = DataRange1d(range_padding=0.0)
        self.plot.grid.grid_line_alpha = 0.3

        self.plot.extra_y_ranges = {
            "b": DataRange1d(range_padding=0),
        }
        self.y_axis_2 = LinearAxis(y_range_name="b", axis_label=self._generate_axis_label(self.unit_b))
        self.plot.add_layout(self.y_axis_2, "right")
        self.y_axis_2.visible = False


class WetstatBokehApp(object):

    def __init__(self, doc) -> None:
        self.doc = doc
        self.plots: List[WetstatPlot] = []
        self.today = datetime.date.today() - datetime.timedelta(days=365)
        self.now = datetime.datetime.now() - datetime.timedelta(days=365)
        self.end = self.now
        self.start = self.end - datetime.timedelta(days=1)
        self.data = None
        self.cds = None
        self.so_rows = []
        self.so_widgets = {}
        self.picker_start = None
        self.picker_end = None
        self.show_legend_toggle = None
        self.hover_tool = None
        self.plot_column: Optional[Column] = None
        self.callback_enabled = True
        self.msg_div: Optional[Div] = None

    def set_new_dbdata(self, db_data: db_model.DbData) -> None:
        time_col = db_data.array[:, db_data.columns.index("Time")]
        istart = np.searchsorted(time_col, self.start, "left")
        iend = np.searchsorted(time_col, self.end, "right")

        data_dict = {db_data.columns[i]: db_data.array[istart:iend, i] for i in range(len(db_data.columns))}
        new = ColumnDataSource(data=data_dict)
        if self.cds:
            self.cds.data = new.data
        else:
            self.cds = new

    def redisplay_lines(self) -> None:
        axes_for_sn = {sn: self.so_widgets[sn]["y_axis"].value for sn in ALL_SHORT_NAMES}  # {Temp1: 1a, Rain: 1b, ..}
        active_for_sn = {sn: self.so_widgets[sn]["active"].active for sn in ALL_SHORT_NAMES}  # {Temp1: True, ...}
        sens_lists = []  # [{a: [Temp1, Temp2], b: [Rain]}, {a: [Humidity], b: []}, {a: [], b: [Pressure]}]
        for sn, axis in axes_for_sn.items():
            if active_for_sn[sn]:
                ax_i, ax_side = axis
                ax_i = int(ax_i)
                while len(sens_lists) < ax_i:
                    sens_lists.append({"a": [], "b": []})
                sens_lists[ax_i - 1][ax_side].append(sn)
        print(f"Current distribution: {pprint.pformat(sens_lists)}")
        self.add_enough_plots(len(sens_lists))
        for i_plot, plot in enumerate(self.plots):
            plot.sensor_list_a.clear()
            plot.sensor_list_b.clear()
            if len(sens_lists) > i_plot:
                plot.sensor_list_a.extend(sens_lists[i_plot]["a"])
                plot.sensor_list_b.extend(sens_lists[i_plot]["b"])
            plot.refresh_lines()
        self.refresh_axis_options()
        self.msg_div.text = "<br>".join(f"{i + 1}, {li}" for i, li in enumerate(sens_lists)) + \
                            "<hr>" + \
                            "<br>".join(f"{plot.nr}={plot.unit_a}|{plot.unit_b}" for plot in self.plots)

    def callback_sensor_active(self, attr, old, new) -> None:
        if self.callback_enabled:
            print("Callback sensor")
            self.redisplay_lines()

    def callback_sensor_axis(self, attr, old, new) -> None:
        if self.callback_enabled:
            print("Callback axis")
            self.redisplay_lines()

    def add_enough_plots(self, at_least_count: int) -> None:
        while at_least_count > len(self.plots):
            print("added new plot")
            self.add_new_plot(len(self.plots) + 1)

    def refresh_axis_options(self) -> None:
        self.callback_enabled = False
        num_plots = len(self.plots)
        for short_name, opts in self.so_widgets.items():
            oldvalue = opts["y_axis"]
            sens = sensor_master.SensorMaster.get_sensor_for_info("short_name", short_name)
            unit = sens.get_unit()
            new_options = []
            for i_plt, plt in enumerate(self.plots):
                if not plt.unit_a or unit == plt.unit_a:
                    new_options.append(f"{i_plt + 1}a")
                if not plt.unit_b or unit == plt.unit_b:
                    new_options.append(f"{i_plt + 1}b")
            for i in range(num_plots + 1, MAX_SUBPLOTS + 1):
                new_options.append(f"{i}a")
                new_options.append(f"{i}b")
            opts["y_axis"].options = new_options
            if oldvalue in new_options:
                opts["y_axis"].value = oldvalue
            else:
                opts["y_axis"].value = new_options[0]
        self.callback_enabled = True

    def callback_show_legend(self, attr, old, new) -> None:
        pass  # self.plot.legend.location = "top_left" if new else "none"  # todo make the legend disappear

    def callback_start_changed(self, attr, old, new) -> None:
        self.callback_date_changed(new, self.end)

    def callback_end_changed(self, attr, old, new) -> None:
        self.callback_date_changed(self.start, new)

    def callback_date_changed(self, new_start, new_end) -> None:
        print("Callback date", new_start, new_end)
        try:
            util.validate_start_end(new_start, new_end)
        except ValueError as e:
            print(e)
            self.picker_start.value = self.start
            self.picker_end.value = self.end
            return
        self.start = util.date_to_datetime(new_start)
        self.end = util.date_to_datetime(new_end, True)
        self.data = db_model.load_data_for_date_range(self.start, self.end, already_existing=self.data)
        time_col = self.data.array[:, self.data.columns.index("Time")]
        data_start = time_col[0]
        data_end = time_col[-1]
        if data_start > self.start:
            self.start = data_start
        if data_end < self.end:
            self.end = data_end

        self.set_new_dbdata(self.data)

    def initialize(self) -> None:

        # self.hover_tool = HoverTool()
        # self.hover_tool.point_policy = "follow_mouse"
        # self.plot.add_tools(self.hover_tool)
        self.plots.append(WetstatPlot(1, self))

        self.data = db_model.load_data_for_date_range(self.start, self.end)
        self.set_new_dbdata(self.data)

        for sens in sensor_master.USED_SENSORS:
            opts = []
            for i in range(1, MAX_SUBPLOTS + 1):
                opts.append(f"{i}a")
                opts.append(f"{i}b")
            active = Toggle(label=sens.get_long_name(),
                            active=sens.get_short_name() in DEFAULT_ACTIVE_SENSORS,
                            background=sens.get_display_color(),  # todo make button white if inactive, else colored
                            width_policy="fixed",
                            width=140,
                            )
            active.on_change("active", self.callback_sensor_active)
            interval = Select(title="",
                              value="Kein",
                              options=["Kein", "Stunde", "Tag", "Woche", "Monat", "Jahr"],
                              width_policy="fixed",
                              width=85,
                              )
            y_axis = Select(title="",
                            value="1a",
                            options=opts,
                            width_policy="fixed",
                            width=70,
                            )
            y_axis.on_change("value", self.callback_sensor_axis)
            self.so_rows.append(row(active, interval, y_axis))
            self.so_widgets[sens.get_short_name()] = {
                "active": active,
                "interval": interval,
                "y_axis": y_axis,
            }

        self.picker_start = DatePicker(title="Start",
                                       min_date=datetime.date(2010, 1, 1),
                                       max_date=self.today - datetime.timedelta(days=1),
                                       width_policy="fixed",
                                       width=150)
        self.picker_end = DatePicker(title="Ende",
                                     min_date=datetime.date(2010, 1, 2),
                                     max_date=self.today,
                                     width_policy="fixed",
                                     width=150)

        self.picker_start.on_change("value", self.callback_start_changed)
        self.picker_end.on_change("value", self.callback_end_changed)

        self.show_legend_toggle = Toggle(label="Legende anzeigen",
                                         active=False,
                                         width_policy="fixed",
                                         width=90,
                                         )
        self.show_legend_toggle.on_change("active", self.callback_show_legend)
        date_range_row = row(self.picker_start, self.picker_end)

        self.msg_div = Div(text=".")

        self.callback_sensor_active("value", 0, 0)
        self.refresh_axis_options()
        self.plot_column = column(*[plt.plot for plt in self.plots])
        self.doc.add_root(row(column(*self.so_rows, date_range_row, self.show_legend_toggle, self.msg_div),
                              self.plot_column,
                              )
                          )

        # self.doc.theme = Theme(filename="theme.yaml")

    @staticmethod
    def create(doc) -> None:
        app = WetstatBokehApp(doc)
        app.initialize()

    def add_new_plot(self, num):
        wetstat_plot = WetstatPlot(num, self)
        self.plots.append(wetstat_plot)
        self.plot_column.children.append(wetstat_plot.plot)


def run_bokeh_server() -> None:
    server = Server({URL: WetstatBokehApp.create}, num_procs=1,
                    allow_websocket_origin=["127.0.0.1:8000", f"localhost:{PORT}"], port=PORT)
    server.start()
    print(f"Opening Bokeh application on http://localhost{URL}:{PORT}")

    server.io_loop.add_callback(server.show, URL)
    server.io_loop.start()


if __name__ == '__main__':
    run_bokeh_server()
