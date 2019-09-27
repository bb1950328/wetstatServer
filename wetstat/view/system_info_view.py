# coding=utf-8
import datetime
import os
import time

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import escape
from django.utils.safestring import mark_safe

from wetstat.common import config, logger
from wetstat.model import system_info as system_info_model, log_parser
from wetstat.model.data_download import DataDownload
from wetstat.sensors import sensor_master
from wetstat.service_manager import service_manager_com
from wetstat.view import views


def system_info(request) -> HttpResponse:
    infos = [{"command": (" ".join(ic.get_command())), "output": mark_safe(ic.get_output())} for ic in
             system_info_model.ALL_INFO_CLASSES]

    context = {"infos": infos}
    return render(request, "wetstat/system/info.html", context)


def system_services(request) -> HttpResponse:
    info = service_manager_com.get_info()
    context = {"services": info.values() if info else None,
               "connected": bool(info)}
    return render(request, "wetstat/system/services.html", context)


def system_log(request: WSGIRequest) -> HttpResponse:
    lvl = request.GET.get("level")
    if not lvl:
        lvl = log_parser.LV_DEBUG

    try:
        limit = int(request.GET.get("limit"))
    except (ValueError, TypeError):
        limit = 100
    parsed = log_parser.parse(level=lvl, max_lines=limit)
    for p in parsed:
        if config.ENDL in p.msg:
            p.msg = escape(p.msg)
            p.msg = mark_safe(p.msg.replace(config.ENDL, "<br>"))

    context = {"log": parsed,
               "levels": log_parser.LEVELS}
    return render(request, "wetstat/system/log.html", context)


def system_download(request) -> HttpResponse:
    now = config.get_date()
    last_month = now - datetime.timedelta(days=30)
    context = {
        "start_date": last_month.strftime("%Y-%m-%d"),
        "end_date": now.strftime("%Y-%m-%d"),
        "columns_available": [[sens.get_short_name(), sens.get_long_name()] for sens in sensor_master.ALL_SENSORS],
    }

    return render(request, "wetstat/system/download.html", context)


def system_real_download(request: WSGIRequest) -> HttpResponse:
    start = time.perf_counter()
    dd = DataDownload()
    try:
        dd.set_start(datetime.datetime.strptime(request.GET.get("start"), "%Y-%m-%d"))
        dd.set_end(datetime.datetime.strptime(request.GET.get("end"), "%Y-%m-%d"))
    except ValueError:
        return views.show_error(request, "Falsches Format für Start/Ende!", "/system/download")
    dd.single_file = "single" in request.GET.keys()
    dd.make_zip = "zip" in request.GET.keys()
    path = dd.prepare_download()
    with open(path, "rb") as out:
        response = HttpResponse(out.read())
    response["Content-Type"] = 'text/csv' if path.endswith(".csv") else "application/zip"
    response["Content-Disposition"] = "attachment; filename=\"" + os.path.basename(path) + "\""
    end = time.perf_counter()
    days = (dd.end - dd.start).days
    logger.log.info(f"prepared data download for {dd.start.date().isoformat()} - {dd.end.date().isoformat()} "
                    f"({days} days) "
                    f"in {round(end - start, 3)} sec.")
    return response
