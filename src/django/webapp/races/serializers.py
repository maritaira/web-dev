from rest_framework import serializers
from .models import Race, Car, RaceParticipant

class RaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = ['name', 'date', 'location', 'num_cars']
        read_only_fields = ["owner", "join_code"]

class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = ['name']
        read_only_fields = ["owner", "images_folder"]
        
class RaceParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = RaceParticipant
        fields = ["id", "race", "car_owner", "car", "joined_at"]