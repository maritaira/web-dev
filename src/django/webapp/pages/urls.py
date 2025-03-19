from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name='pages'

urlpatterns = [
    path("", views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_pg, name='login'),
    path('videos/', views.all_videos, name='all_videos'),
    path('create_acc/', views.create_acc, name='create_acc'),
    path('all_cars/', views.all_cars, name='all_cars'),
    path('upcoming_races/', views.upcoming_races, name='upcoming_races'),
    path('display_images/', views.display_images, name="display_images"),
    path('play_video/', views.play_video, name="play_video"),
    path('upload_image/', views.dashboard, name='upload_image')
]