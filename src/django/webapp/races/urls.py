from django.urls import path
from . import views

urlpatterns = [
    path('create-race/', views.CreateRaceView.as_view(), name='create_race'),
    path('add-car/', views.AddCarView.as_view(), name='add_car'),
    path('join-race/', views.JoinRaceView.as_view(), name='join_race'),
    path("races/<str:race_name>/cars/", views.ListCarsInRaceView.as_view(), name="cars-in-race"),
    path("cars/<str:car_name>/races/", views.ListRacesCarJoinedView.as_view(), name="races-car-joined"),
    path("users/<str:username>/races/", views.ListRacesUserJoinedView.as_view(), name="races-user-joined"),
    path("users/<str:username>/cars/", views.ListUserCarsView.as_view(), name="cars-user-owns"),
    path('races/my_races/',views.RaceOwnerMyRacesView.as_view(), name="raceowner-myraces"),
    path('carowner/my_races/',views.CarOwnerMyRacesView.as_view(), name="carowner-myraces")
]

