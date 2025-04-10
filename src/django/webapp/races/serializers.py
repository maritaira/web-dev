from rest_framework import serializers
from .models import Race, Car, RaceParticipant

class RaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = ['id', 'name', 'date', 'location', 'num_cars']
        read_only_fields = ["owner"]

class CarSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Car
        fields = ['id', 'name', 'is_eligible', 'owner_username']
        read_only_fields = ["owner", "images_folder"]
        
class RaceParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = RaceParticipant
        fields = ["id", "race", "car_owner", "car", "joined_at"]