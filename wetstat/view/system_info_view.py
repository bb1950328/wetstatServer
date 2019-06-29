# coding=utf-8
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from wetstat.model import system_info as system_info_model, log_parser
from wetstat.service_manager import service_manager_com


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


def system_log(request) -> HttpResponse:
    context = {"log": log_parser.parse()}
    return render(request, "wetstat/system/log.html", context)


def system_download(request) -> HttpResponse:
    # TODO
    return render(request, "wetstat/system/download.html")
