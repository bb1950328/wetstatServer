# coding=utf-8
from django.urls import path

from wetstat.view import views

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

    path("custom", views.custom),
    path("custom.html", views.custom),

    path("custom_v2", views.custom_v2),
    path("custom_v2.html", views.custom_v2),

    path("customplot", views.customplot),
    path("show_plot.html", views.customplot),

    path("generate_plot", views.generate_plot),
    path("generate_plot.html", views.generate_plot),

    path("progress", views.progress),
    path("progress.html", views.progress),

    path("system", views.system),
    path("system.html", views.system),
]
