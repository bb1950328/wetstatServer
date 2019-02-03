import datetime
import random

from django.shortcuts import render


# Create your views here.
from wetstat import csvtools, models


def get_date() -> datetime.datetime:
    # for development
    return datetime.datetime.now() - datetime.timedelta(days=365)
    # noinspection PyUnreachableCode
    return datetime.datetime.now()


def index(request):
    now = models.get_nearest_record(get_date())
    yesterday = models.get_nearest_record(get_date() - datetime.timedelta(days=1))
    lastmonth = models.get_nearest_record(get_date() - datetime.timedelta(days=30))
    lastyear = models.get_nearest_record(get_date() - datetime.timedelta(days=365))

    sarr = []
    for i, name in enumerate(now.keys()):
        if name == "Time":
            continue
        change = (now.get(name) / yesterday.get(name)) - 1
        if change > 1.15:
            img = "arrow_up_transparent.png"
        elif change < 0.95:
            img = "arrow_down_transparent.png"
        else:
            img = "arrow_neutral_transparent.png"
        val = now.get(name)
        if len(str(val)) > 9:  # too long to display
            sv = str(val)
            val = sv[:3] + "..." + sv[-3:]
        sarr.append(
            {
                "name": name,
                "value": val,
                "img": img,
                "before_month": lastmonth.get(name, "?"),
                "before_year": lastyear.get(name, "?"),
            }
        )
    sensors = {"array": sarr}
    context = {"sensors": sensors}
    return render(request, "wetstat/index.html", context)


def week(request):
    return render(request, "wetstat/week.html")


def month(request):
    return render(request, "wetstat/month.html")


def year(request):
    return render(request, "wetstat/year.html")
