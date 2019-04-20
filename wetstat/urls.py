# coding=utf-8
from django.urls import path

from wetstat import views

urlpatterns = [
    path("", views.index),
    path("week", views.week),
    path("week.html", views.week),
    path("month", views.month),
    path("month.html", views.month),
    path("year", views.year),
    path("year.html", views.year),
    path("custom", views.custom),
    path("custom.html", views.custom),
    path("customplot", views.customplot),
    path("customplot.html", views.customplot),
    path("generate_plot", views.generate_plot),
    path("generate_plot.html", views.generate_plot),
]
