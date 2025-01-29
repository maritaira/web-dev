from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the pages view.")


def dashboard(request):
    return render(request, 'dashboard.html')

def all_videos(request):
    return render(request, 'all_videos.html')

def login_pg(request):
    return render(request, 'login.html')

def create_acc(request):
    return render(request, 'create_acc.html')
def all_cars(request):
    return render(request, 'all_cars.html')
def upcoming_races(request):
    return render (request, 'upcoming_races.html')