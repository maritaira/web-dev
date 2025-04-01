from django.urls import path
from .views import start_training

from . import views

urlpatterns = [
    path('start-training/', start_training, name='start_training'),
]