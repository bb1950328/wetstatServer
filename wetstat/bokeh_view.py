# coding=utf-8
import datetime
from typing import Optional, List

import numpy as np
from bokeh.client import pull_session
from bokeh.embed import server_session
from bokeh.layouts import column, row
from bokeh.models import DataRange1d, Select, Toggle, ColumnDataSource, HoverTool, LinearAxis
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

ALL_SHORT_NAMES = sensor_master.SensorMaster.get_used_sensor_short_names()

URL = "/wetstat_bokeh"
PORT = 5006
DEFAULT_ACTIVE_SENSORS = ["DigitalTemp", "Humidity"]


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
        self._unit_a = new
        self.plot.yaxis.axis_label = self._generate_axis_label(self._unit_a)

    @property
    def unit_b(self) -> str:
        return self._unit_b

    @unit_b.setter
    def unit_b(self, new) -> None:
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
        in_list = {*self.sensor_list_a, *self.sensor_list_b}
        in_renderer = {*self._renderers_a.keys(), *self._renderers_b.keys()}
        all_sensors = {*in_list, *in_renderer}
        for sn in all_sensors:
            if sn not in in_list:
                if sn in self._renderers_a.keys():
                    self._renderers_a[sn].visible = False
                elif sn in self._renderers_b.keys():
                    self._renderers_b[sn].visible = False
            else:
                moved = False
                if sn in self.sensor_list_a and sn in self._renderers_b:
                    self._renderers_b[sn].visible = False
                    if sn in self._renderers_a:
                        self._renderers_a[sn].visible = True
                    else:
                        moved = True
                if sn in self.sensor_list_b and sn in self._renderers_a:
                    self._renderers_a[sn].visible = False
                    if sn in self._renderers_b:
                        self._renderers_b[sn].visible = True
                    else:
                        moved = True

                if sn not in in_renderer or moved:
                    if sn in self.app.data.columns:
                        rlist = self._renderers_a if sn in self.sensor_list_a else self._renderers_b
                        sens = sensor_master.SensorMaster.get_sensor_for_info("short_name", sn)
                        is_a = rlist == self._renderers_a
                        rlist[sn] = self.plot.line("Time", sn, source=self.app.cds,
                                                   color=sens.get_display_color(),
                                                   # legend_label=sens.get_long_name(),
                                                   y_range_name="default" if is_a else "b",
                                                   )
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
                    else:
                        if sn in self._renderers_b:
                            self._renderers_b[sn].visible = True
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
            tools=["xpan", "xwheel_zoom", "hover", "crosshair", "reset", "save"]
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
        # self.line_renderers = {}
        # self.axis_units: List[Dict[str, str]] = []  # [{"a": "°C", "b": "%"}, {"a": "mm", "b": "hpa"}]
        self.so_rows = []
        self.so_widgets = {}
        self.picker_start = None
        self.picker_end = None
        self.show_legend_toggle = None
        self.hover_tool = None
        self.plot_column = None

    def set_new_dbdata(self, db_data: db_model.DbData) -> None:
        time_col = db_data.array[:, db_data.columns.index("Time")]
        istart = np.searchsorted(time_col, self.start, "left")
        iend = np.searchsorted(time_col, self.end, "right")
        # istart = 0
        # iend = len(db_data.array)
        # while db_data.array[istart, db_data.columns.index("Time")] < self.start:
        #     istart += 1
        # while db_data.array[iend, db_data.columns.index("Time")] > self.end:
        #     iend -= 1
        # istart -= 1
        # iend += 1

        data_dict = {db_data.columns[i]: db_data.array[istart:iend, i] for i in range(len(db_data.columns))}
        new = ColumnDataSource(data=data_dict)
        if self.cds:
            self.cds.data = new.data
        else:
            self.cds = new

    def callback_sensor_active(self, attr, old, new) -> None:
        print("Callback sensor")
        tooltips = []
        for sn in ALL_SHORT_NAMES:
            act = self.so_widgets[sn]["active"].active
            axi = self.so_widgets[sn]["y_axis"].value
            sens = sensor_master.SensorMaster.get_sensor_for_info("short_name", sn)
            unit = sens.get_unit()

            i_plt = int(axi[0]) - 1
            slist = self.plots[i_plt].sensor_list_a
            other_list = self.plots[i_plt].sensor_list_b
            if axi[1] == "b":
                slist, other_list = other_list, slist
            if act:
                if sn not in slist:
                    slist.append(sn)
                    if sn in other_list:
                        other_list.remove(sn)
            else:
                if sn in slist:
                    slist.remove(sn)
            self.plots[i_plt].refresh_lines()
            tooltips.append((sens.get_long_name(), f"@{sens.get_short_name()}"))

        for plt in self.plots:
            for to in plt.plot.tools:
                if isinstance(to, HoverTool):
                    to.tooltips = tooltips
                    break

    def callback_sensor_axis(self, attr, old, new) -> None:
        axes = {sn: self.so_widgets[sn]["y_axis"].value for sn in ALL_SHORT_NAMES}
        found = False
        for i, plt in enumerate(self.plots):
            for sn in plt.sensor_list_a + plt.sensor_list_b:
                if axes[sn] != f"{i + 1}a":
                    # remove on old axis
                    if sn in plt.sensor_list_a:
                        plt.sensor_list_a.remove(sn)
                    else:
                        plt.sensor_list_b.remove(sn)

                    # find new axis and add
                    i_ax_plt = int(axes[sn][0]) - 1
                    while i_ax_plt >= len(self.plots):
                        self.add_new_plot(len(self.plots) + 1)
                    ax_plt = self.plots[i_ax_plt]
                    unit = sensor_master.SensorMaster.get_sensor_for_info("short_name", sn).get_unit()
                    if axes[sn][1] == "a":
                        if ax_plt.unit_a and unit != ax_plt.unit_a:
                            raise ValueError(f"This axis is already occupied by unit '{ax_plt.unit_a}' !!!")
                        ax_plt.unit_a = unit
                        ax_plt.sensor_list_a.append(sn)
                    else:
                        if ax_plt.unit_b and unit != ax_plt.unit_b:
                            raise ValueError(f"This axis is already occupied by unit '{ax_plt.unit_b}' !!!")
                        ax_plt.unit_b = unit
                        ax_plt.sensor_list_b.append(sn)

                    ax_plt.refresh_lines()

                    found = True
                    break
            if found:
                break
        if not found:
            raise ValueError("Nothing changed?!?")

    def refresh_axis_options(self):
        pass  # TODO

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
                            options=["1a", "1b", "2a", "2b", "2a", "3b"],
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

        self.callback_sensor_active("value", 0, 0)
        self.plot_column = column(*[plt.plot for plt in self.plots])
        self.doc.add_root(row(column(*self.so_rows, date_range_row, self.show_legend_toggle),
                              self.plot_column,
                              )
                          )

        # self.doc.theme = Theme(filename="theme.yaml")

    @staticmethod
    def create(doc) -> None:
        # start_bokeh_server_if_not_running()
        app = WetstatBokehApp(doc)
        app.initialize()

    def add_new_plot(self, num):
        self.plots.append(WetstatPlot(num, self))
        self.plot_column  # TODO add new plot to this layout to display it


def run_bokeh_server() -> None:
    server = Server({URL: WetstatBokehApp.create}, num_procs=1,
                    allow_websocket_origin=["127.0.0.1:8000", f"localhost:{PORT}"], port=PORT)
    server.start()
    print(f"Opening Bokeh application on http://localhost{URL}:{PORT}")

    server.io_loop.add_callback(server.show, URL)
    server.io_loop.start()


if __name__ == '__main__':
    run_bokeh_server()
