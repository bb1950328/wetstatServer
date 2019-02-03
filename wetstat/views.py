import datetime

from django.shortcuts import render


# Create your views here.

def getDate() -> datetime.date:
    # for development
    return datetime.date(2018, 6, 3)
    # noinspection PyUnreachableCode
    return datetime.date.today()

def index(request):
    return render(request, "wetstat/index.html")


def week(request):
    return render(request, "wetstat/week.html")


def month(request):
    return render(request, "wetstat/month.html")


def year(request):
    return render(request, "wetstat/year.html")
