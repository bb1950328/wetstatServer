import datetime
import random

from django.shortcuts import render


# Create your views here.

def get_date() -> datetime.date:
    # for development
    return datetime.date.today() - datetime.timedelta(days=365)
    # noinspection PyUnreachableCode
    return datetime.date.today()


def index(request):
    imgpaths = ["arrow_up_transparent.png",
                "arrow_neutral_transparent.png",
                "arrow_down_transparent.png"]
    random.shuffle(imgpaths)
    ra = {"num1": random.randint(-200, 380) / 10,
          "num2": random.randint(-200, 380) / 10,
          "imgname": imgpaths[0],
          }
    sarr = [
        {
            "name": "Temperatur 1",
            "value": random.randint(-200, 380) / 10,
            "before_month": random.randint(-200, 380) / 10,
            "before_year": random.randint(-200, 380) / 10,
        },
        {
            "name": "Temperatur 2",
            "value": random.randint(-200, 380) / 10,
            "before_month": random.randint(-200, 380) / 10,
            "before_year": random.randint(-200, 380) / 10,
        }
    ]
    sensors = {"array": sarr}
    context = {"random": ra, "sensors": sensors}
    return render(request, "wetstat/index.html", context)


def week(request):
    return render(request, "wetstat/week.html")


def month(request):
    return render(request, "wetstat/month.html")


def year(request):
    return render(request, "wetstat/year.html")
