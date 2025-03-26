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
        fields = "__all__"
        
class RaceParticipantSerializer(serializers.ModelSerializer):
    car_name = serializers.ReadOnlyField(source='car.name')
    owner_username = serializers.ReadOnlyField(source='car_owner.username')
    
    class Meta:
        model = RaceParticipant
        fields = ["id", "car_name", "owner_username", "joined_at"]