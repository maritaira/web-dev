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
    path('create_race/', views.create_race, name='create_race'),
    path('new_car/', views.new_car, name='new_car'),
    path('all_cars/', views.all_cars, name='all_cars'),
    path('display_images/', views.display_images, name="display_images"),
    path('play_video/', views.play_video, name="play_video"),
    path('upload_image/', views.dashboard, name='upload_image'),
    path('raceownerDash/', views.raceDash, name='raceownerDash')
]