from django.urls import path

from wetstat import views

urlpatterns = [
    path("", views.index),
    path("week", views.week),
    path("month", views.month),
    path("year", views.year),
    path("custom", views.custom),
]
