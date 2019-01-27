from django.shortcuts import render


# Create your views here.

def index(request):
    return render(request, "wetstat/index.html")


def week(request):
    return render(request, "wetstat/week.html")


def month(request):
    return render(request, "wetstat/month.html")


def year(request):
    return render(request, "wetstat/year.html")
