# coding=utf-8
from django.urls import path

from wetstat.view import views, system_info_view

urlpatterns = [
    path("", views.index),
    path("index", views.index),
    path("index.html", views.index),

    path("week", views.week),
    path("week.html", views.week),

    path("month", views.month),
    path("month.html", views.month),

    path("year", views.year),
    path("year.html", views.year),

    path("custom_v2", views.custom_v2),
    path("custom_v2.html", views.custom_v2),

    path("customplot", views.customplot),
    path("show_plot.html", views.customplot),

    path("generate_plot", views.generate_plot),
    path("generate_plot.html", views.generate_plot),

    path("progress", views.progress),
    path("progress.html", views.progress),

    path("system", system_info_view.system_info),
    path("system/info.html", system_info_view.system_info),

    path("system/services", system_info_view.system_services),
    path("system/services.html", system_info_view.system_services),

    path("system/log", system_info_view.system_log),
    path("system/log.html", system_info_view.system_log),

    path("system/download", system_info_view.system_download),
    path("system/download.html", system_info_view.system_download),

    path("system/real_download", system_info_view.system_real_download),
    path("system/real_download.html", system_info_view.system_real_download),
]
