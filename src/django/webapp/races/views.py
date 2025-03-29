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
from media.models import Image
from media.serializers import ImageSerializer
from webapp.storages import RacesBucketStorage, CarsBucketStorage
import uuid
import json

class CreateRaceView(generics.CreateAPIView):
    serializer_class = RaceSerializer
    permission_classes = [IsRaceOwner]
    queryset = Race.objects.all()
    # permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # print("In perform_create for CreateRace")
        print(f"Checking user: {self.request.user.username}")
        print(f"race data: {self.request.data}")
        
        serializer = RaceSerializer(data=self.request.data)
        if serializer.is_valid():
            # print(f"Saving serializer with owner {self.request.user}")
            race = serializer.save(owner=self.request.user)
            # print(f"race.id: {race.id}; race_name:{race.name}; join_code: {race.join_code}")
        
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
        

class AddCarView(generics.CreateAPIView):
    serializer_class = CarSerializer
    permission_classes = [IsCarOwner]
    
    def perform_create(self, serializer):
        print("In perform_create for AddCar")
        print(f"Checking user: {self.request.user.username}")
        print(f"Car data: {self.request.data}")
        print(f"Type of request.user: {type(self.request.user)}")
        print(self.request.user)
        
        
        serializer = CarSerializer(data=self.request.data)
        if serializer.is_valid():
            # print(f"Saving serializer with owner {self.request.user}")
            name = serializer.validated_data['name']
            images_folder = f"{self.request.user.username}/{name}/images"
            car = serializer.save(owner=self.request.user, images_folder=images_folder)
            print("Car serializer saved")
            
            
            image_files = self.request.FILES.getlist('images')
            image_instances = []
            print(image_files)
            
            try:
                storage = CarsBucketStorage()
            except Exception as e:
                print(f"Error when initializing CarsBucketStorage: {str(e)}")
                return
            
            id_token = self.request.headers.get('Authorization', '').split("Bearer ")[-1]
            print(f"ID Token: {id_token}")
            
            storage._get_client(self.request.user.cognito_identity_id, id_token)
            
            if not storage.s3_client:
                print("s3 client not retrieved successfully")
                return
              
            for image in image_files:
                print("Creeating Image object without image")
                # image_instance =Image.objects.create(car=car, image=image)
                image_instance = Image(car=car, image=image)
                print("Assigning image storage")
                image_instance.image.storage = storage  # Assign storage dynamically
                # print("saving image name and file")
                # image_instance.image.save(image.name, image, save=False)
                print("Saving image instance")
                image_instance.save()
                image_instances.append(image_instance)
               
            print("Initializing image serializer") 
            image_serializer = ImageSerializer(image_instances,  many=True)
            response = Response({
                    "message": "Images uploaded successfully",
                    "data": image_serializer.data
                    }, status=status.HTTP_201_CREATED)
            
            if response.status_code != status.HTTP_201_CREATED:
                print("Image upload failed")
                return Response({'status': 'error', 'message': 'Image upload failed'}, status=status.HTTP_400_BAD_REQUEST)

            print("Car and images successfully added")
            return Response({'status': 'success', 'message': 'Car and images added successfully.'}, status=status.HTTP_201_CREATED)

        else:
            return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


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
