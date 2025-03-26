from django.shortcuts import render
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Race, Car, RaceParticipant
from .serializers import RaceSerializer, CarSerializer, RaceParticipantSerializer
from accounts.permissions import IsCarOwner, IsRaceOwner
from webapp.storages import RacesBucketStorage
import uuid
import json

class CreateRaceView(generics.CreateAPIView):
    serializer_class = RaceSerializer
    permission_classes = [IsRaceOwner]
    queryset = Race.objects.all()
    # permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # try:
        #     print("In perform_create for CreateRace")
        #     print(f"race data: {request.data}")
        #     return Response({"message": "success"}, status=status.HTTP_201_CREATED)
        # except Exception as e:
        #     print("Error:", str(e))
        #     return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        print("In perform_create for CreateRace")
        print(f"Checking user: {self.request.user.username}")
        # race_data = {
        #     "name": request.data.get("name"),
        #     "location": request.data.get("location"),
        #     "date": request.data.get("date"),
        #     "num_cars": request.data.get("num_cars"),
        # }
        print(f"race data: {self.request.data}")
        # return Response({"message": "success"})
        
        serializer = RaceSerializer(data=self.request.data)
        print("serializer created successfully")
        if serializer.is_valid():
            print(f"Saving serializer with owner {self.request.user}")
            race = serializer.save(owner=self.request.user)
            print(f"race.id: {race.id}; race_name:{race.name}; join_code: {race.join_code}")
        
        # # create s3 directory in races bucket
        # race_storage = RacesBucketStorage()
        # race_directory = f"{race.name}/"

        # # add metadata JSON file in the second bucket
        # metadata = {
        #     "name": race.name,
        #     "location": race.location,
        #     "date": str(race.date),
        #     "num_cars": str(race.num_cars),
        #     "owner": race.owner.username
        # }
        # race_storage.save(race_directory + "metadata.json", ContentFile(json.dumps(metadata)))
        # print("Created directory in S3 bucket")
            return Response({
                "message": "Race created successfully",
                "race_id": race.id, 
                "join_code": race.join_code,
                "race": serializer.data
                }, status=status.HTTP_201_CREATED)
        print("Serializer not valid")    
        return Response({
            "message": "Error creating race.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        

class JoinRaceView(generics.CreateAPIView):
    serializer_class = RaceParticipantSerializer
    # permission_classes = [IsAuthenticated, IsCarOwner]
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        print("In create for JoinRace")
        user = request.user # assuming authentication is set up
        join_code = request.data.get("join_code")
        car_id = request.data.get("car_id")
        
        race = Race.objects.filter(join_code=join_code).first()
        car = get_object_or_404(Car, id=car_id, owner=user) # ensure user owns car
        
        if not race:
            print("invalid join code")
            return Response({"error": "Invalid join code"}, status=status.HTTP_400_BAD_REQUEST)
        
        if RaceParticipant.objects.filter(race=race, car_owner=user, car=car).exists():
            print(f"Car {car.name} is already in race {race.name}")
            return Response({"error": f"Car {car.name} is already in race {race.name}"}, status=status.HTTP_400_BAD_REQUEST)

        RaceParticipant.objects.create(race=race, user=request.user)
        return Response({"message": "Successfully joined race"}, status=status.HTTP_201_CREATED)

class ListCarsInRaceView(generics.ListAPIView):
    serializer_class = RaceParticipantSerializer
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    def get_queryset(self):
        race_name = self.kwargs["race_name"]
        try:
            race = Race.objects.get(name=race_name)
            return Car.objects.filter(races__race=race)
        except Race.DoesNotExist:
            return Car.objects.none()  # Return an empty queryset if race is not found
    
class ListRacesUserJoinedView(generics.ListAPIView):
    serializer_class = RaceSerializer
    permission_classes = [IsCarOwner]

    def get_queryset(self):
        user_cars = self.request.user.cars.all()  # Get all cars owned by the user
        return Race.objects.filter(participants__car__in=user_cars).distinct()  # Fetch races where user's cars have joined

#    List all races a specific car has joined
class ListRacesCarJoinedView(generics.ListAPIView):
    serializer_class = RaceSerializer
    # permission_classes = [IsAuthenticated, IsCarOwner]
    permission_classes = [AllowAny]

    def get_queryset(self):
        car_name = self.kwargs["car_name"]
        try:
            car = Car.objects.get(name=car_name)
            # Find races this car is in
            return Race.objects.filter(participants__car=car).distinct()
        except Car.DoesNotExist:
            print("car not found")
            return Race.objects.none()  # return empty queryset if car not found
        
        
#   List all cars owned by the authenticated user
class ListUserCarsView(generics.ListAPIView):
    serializer_class = CarSerializer
    # permission_classes = [IsAuthenticated, IsCarOwner]
    permission_classes = [AllowAny]

    def get_queryset(self):
        return self.request.user.cars.all()
