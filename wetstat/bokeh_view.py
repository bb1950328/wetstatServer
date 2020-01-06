# coding=utf-8
import datetime

import numpy as np
from bokeh.client import pull_session
from bokeh.embed import server_session
from bokeh.layouts import column, row
from bokeh.models import DataRange1d, Select, Toggle, ColumnDataSource, HoverTool
from bokeh.models.widgets import DatePicker
from bokeh.plotting import figure
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
DEFAULT_ACTIVE_SENSORS = ["DigitalTemp", "Humidity"]


def bkapp_view(request: WSGIRequest) -> HttpResponse:
    with pull_session(url=f"http://localhost:5006{URL}") as session:
        # update or customize that session
        session.document.roots[0].children[1].title.text = "Special Sliders For A Specific User!"

        # generate a script to load the customized session
        script = server_session(session_id=session.id, url=f'http://localhost:5006{URL}')

        # use the script in the rendered page
        context = {
            "script": mark_safe(script),
            **views.get_base_context("bokeh")
        }
        return render(request, "wetstat/bokeh_embed.html", context)


class WetstatBokehApp(object):

    def __init__(self, doc) -> None:
        self.doc = doc
        self.plot = None
        self.today = datetime.date.today() - datetime.timedelta(days=365)
        self.now = datetime.datetime.now() - datetime.timedelta(days=365)
        self.end = self.now
        self.start = self.end - datetime.timedelta(days=1)
        self.data = None
        self.cds = None
        self.line_renderers = {}
        self.so_rows = []
        self.so_widgets = {}
        self.picker_start = None
        self.picker_end = None
        self.show_legend_toggle = None
        self.hover_tool = None

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

    def callback_sensor(self, attr, old, new) -> None:
        print("Callback sensor")
        tooltips = []
        for sn in ALL_SHORT_NAMES:
            a = self.so_widgets[sn]["active"]
            if a.active:
                if sn not in self.line_renderers.keys():  # box got activated for the first time
                    self.create_line(sn)
                else:
                    self.line_renderers[sn].visible = True
                sens = sensor_master.SensorMaster.get_sensor_for_info("short_name", sn)
                tooltips.append((sens.get_long_name(), sens.get_short_name()))
            else:
                if sn in self.line_renderers.keys():
                    self.line_renderers[sn].visible = False
        self.hover_tool.tooltips = tooltips

    def callback_show_legend(self, attr, old, new) -> None:
        self.plot.legend.location = "top_left" if new else "none"  # todo make the legend disappear

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
        self.plot = figure(
            title='Auswertung',
            x_axis_type="datetime",
            x_axis_label='Zeit',
            tools=["xpan", "xwheel_zoom", "hover", "reset", "save"]
            # toolbar_location=None,
        )
        self.plot.x_range = DataRange1d(range_padding=0.0)
        self.plot.grid.grid_line_alpha = 0.3

        self.data = db_model.load_data_for_date_range(self.start, self.end)
        self.set_new_dbdata(self.data)

        for sens in sensor_master.USED_SENSORS:
            active = Toggle(label=sens.get_long_name(),
                            active=sens.get_short_name() in DEFAULT_ACTIVE_SENSORS,
                            background=sens.get_display_color(),  # todo make button white when inactive, else colored
                            width_policy="fixed",
                            width=140,
                            )
            active.on_change("active", self.callback_sensor)
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

        # slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days")
        # slider.on_change('value', callback)

        self.callback_sensor("value", 0, 0)
        self.hover_tool = HoverTool()
        self.plot.add_tools(self.hover_tool)
        self.doc.add_root(row(column(*self.so_rows, date_range_row, self.show_legend_toggle), self.plot))

        # doc.theme = Theme(filename="theme.yaml")

    def create_line(self, short_name) -> None:
        if short_name in self.data.columns:
            sens = sensor_master.SensorMaster.get_sensor_for_info("short_name", short_name)
            ret = self.plot.line("Time", short_name, source=self.cds,
                                 color=sens.get_display_color(),
                                 legend=sens.get_long_name(),
                                 )
            self.line_renderers[short_name] = ret
        else:
            print(f"no data found for {short_name}!!!")

    @staticmethod
    def create(doc) -> None:
        app = WetstatBokehApp(doc)
        app.initialize()


if __name__ == '__main__':
    server = Server({URL: WetstatBokehApp.create}, num_procs=1,
                    allow_websocket_origin=["127.0.0.1:8000", "localhost:5006"])
    server.start()
    print(f'Opening Bokeh application on http://localhost{URL}:5006')

    server.io_loop.add_callback(server.show, URL)
    server.io_loop.start()
