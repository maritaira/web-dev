from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_pg, name='login'),
    path('videos/', views.all_videos, name='all_videos'),
    path('create_acc/', views.create_acc, name='create_acc'),
    path('create_race/', views.create_race, name='create_race'),
    path('all_cars/', views.all_cars, name='all_cars'),
    path('upcoming_races/', views.upcoming_races, name='upcoming_races'),
    path('images/', views.upload_image, name='upload_image'),
    path('display_images/', views.display_images, name="display_images"),
    path('play_video/', views.play_video, name="play_video")
]