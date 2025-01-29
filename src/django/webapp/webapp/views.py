# projectApp/views.py
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, World!")  # Test view
