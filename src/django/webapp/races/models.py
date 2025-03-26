from django.db import models
from django.conf import settings
import uuid

# Create your models here.

class Race(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    date = models.DateField()
    num_cars = models.IntegerField()
    # links users to races they own (user.races)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="races")
    join_code = models.UUIDField(default=uuid.uuid4, unique=True)
    # need video field most likely
    
    def __str__(self):
        return f"{self.name} - {self.date}"
    
class Car(models.Model):
    name = models.CharField(max_length=255)
    # links users to cars (user.cars)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cars")

    def __str__(self):
        return f"{self.name}"

class RaceParticipant(models.Model):
    # links race participant to race (race.participants)
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="participants")
    # tracks user (user.races_joined)
    car_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="races_joined")
    # ensures race participant is linked to a specific car (car.race_participations)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="race_participations")
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('race', 'car_owner')

    def __str__(self):
        return f"{self.car} in {self.race.name}"