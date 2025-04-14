from django.shortcuts import render
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Race, Car, RaceParticipant
from .serializers import RaceSerializer, CarSerializer, RaceParticipantSerializer
from accounts.permissions import IsCarOwner, IsRaceOwner
from accounts.auth_backends import CognitoJWTAuthentication
from media.views import ImageViewSet
from media.models import Image
from media.serializers import ImageSerializer
from webapp.storages import RacesBucketStorage
import uuid
import json

class CreateRaceView(generics.CreateAPIView):
    serializer_class = RaceSerializer
    permission_classes = [IsRaceOwner]
    queryset = Race.objects.all()
    # permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        print(f"Checking user: {request.user.username}")
        print(f"Race data: {request.data}")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        race = serializer.save(owner=request.user)

        response_data = {
            "message": "Race created successfully",
            "race_id": race.id,
            "race": serializer.data
        }

        print("Custom Response:", response_data)
        return Response(response_data, status=status.HTTP_201_CREATED)

        

class AddCarView(generics.CreateAPIView):
    serializer_class = CarSerializer
    permission_classes = [IsCarOwner]
    
    def perform_create(self, serializer):
        print("In perform_create for AddCar")
        print(f"Checking user: {self.request.user.username}")
        print(f"Car data: {self.request.data}")
        name = self.request.data.get('name')
        
        # Check if a car with the same name already exists for this user
        if Car.objects.filter(owner=self.request.user, name=name).exists():
            print(f"User {self.request.user.username} already owns a car named '{name}'")
            raise serializers.ValidationError({"message": "You already own a car with this name. Please try again with a new car name."})
        
        serializer = CarSerializer(data=self.request.data)
        if serializer.is_valid():
            # print(f"Saving serializer with owner {self.request.user}")
            image_files = self.request.FILES.getlist('images')
            is_eligible = len(image_files) >= 25
            name = serializer.validated_data['name']
            images_folder = f"{self.request.user.username}/{name}/images"
            
            car = serializer.save(
                owner=self.request.user, 
                images_folder=images_folder,
                is_eligible=is_eligible
                )
            print("Car serializer saved")
            
            
            
            image_instances = []
            
            for image in image_files:
                image_instance = Image.objects.create(car=car, image=image)
                image_instances.append(image_instance)
                
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

class AddRaceParticipantsView(generics.CreateAPIView):
    serializer_class = RaceParticipantSerializer
    permission_classes = [IsRaceOwner]
    
    def post(self, request):
        # print("IN AddRacePArticipants view")
        race_id = request.data.get('race_id')
        car_ids = request.data.get('car_ids')

        if not race_id or not car_ids:
            print("You need a race id and at least one car id")
            return Response({"detail": "Missing race_id or car_ids."}, status=status.HTTP_400_BAD_REQUEST)
        
        race = get_object_or_404(Race, id=race_id)
        
        created_participants = []
        errors = []
        
        for car_id in car_ids:
            car = Car.objects.filter(id=car_id).first()
            if not car:
                errors.append(f"Car ID {car_id} does not exist.")
                continue

            if RaceParticipant.objects.filter(race=race, car=car).exists():
                errors.append(f"Car ID {car_id} is already registered.")
                continue

            participant = RaceParticipant.objects.create(race=race, car=car, car_owner=car.owner)
            created_participants.append({
                "race": race.id,
                "car": car.id,
                "participant_id": participant.id
            })
        
        if not errors:
            return Response({
                "success": True, 
                "created": created_participants
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "errors": errors
        }, status=status.HTTP_400_BAD_REQUEST)
            

class JoinRaceView(generics.CreateAPIView):
    serializer_class = RaceParticipantSerializer
    permission_classes = [IsCarOwner]

    def create(self, request):
        print("In create for JoinRace")
        user = request.user # assuming authentication is set up
        print(user)
        join_code = request.data.get("join_code")
        car_id = request.data.get("car_id")
        print(f"Attempting to find race using join_code {join_code} for car_id {car_id}")
        race = Race.objects.filter(join_code=join_code).first()
        car = get_object_or_404(Car, id=car_id, owner=user) # ensure user owns car
        print("Found car")
        
        if not race:
            print("Invalid join code")
            return Response({"error": "Invalid join code"}, status=status.HTTP_400_BAD_REQUEST)
        
        if RaceParticipant.objects.filter(race=race, car_owner=user, car=car).exists():
            print(f"Car {car.name} is already in race {race.name}")
            return Response({"error": f"Car {car.name} is already in race {race.name}"}, status=status.HTTP_400_BAD_REQUEST)

        RaceParticipant.objects.create(race=race, car_owner=user, car=car)
        print("RaceParticipant successfully created")
        print(f"User {user.username}'s Races: {user.races_joined.all()}")
        print(f"Car {car.name}'s Races: {car.race_participations.all()}")
        return Response({"success": True, "message": "Successfully joined race"}, status=status.HTTP_201_CREATED)


#   List all the Races a RaceOwner Owns and All the Participating Cars
class RaceOwnerMyRacesView(generics.ListAPIView):
    serializer_class = RaceParticipantSerializer
    permission_classes = [IsRaceOwner]
    
    def get(self, request, *args, **kwargs):
        raceowner = request.user
        print(f"In RaceOwnerMyRacesView for raceowner: {raceowner}")
        races = Race.objects.filter(owner=raceowner)
        print(f"Races {raceowner} owns: {races}")
        
        race_list = {}
        
        for race in races:
            participants = RaceParticipant.objects.filter(race=race)
            
            cars_and_owners = [
                {
                    "car": participant.car.name, 
                    "owner": participant.car_owner.username, 
                    "firstname": participant.car_owner.name, 
                    "lastname": participant.car_owner.lastname,
                    "email": participant.car_owner.email,
                    "id": participant.car.id
                } for participant in participants
            ]
            
            race_list[race.name] = {
                "details": {
                    "location": race.location,
                    "date": race.date.strftime("%Y-%m-%d"),  # Formatting date for JSON
                    "num_cars": race.num_cars,
                    "id": race.id
                },
                "cars": cars_and_owners
            }
        print(race_list)
            
        return Response(race_list)
    
#   List all the Races a CarOwner has Joined and Their Cars In Them
class CarOwnerMyRacesView(generics.ListAPIView):
    serializer_class = RaceParticipantSerializer
    permission_classes = [IsCarOwner]
    
    def get(self, request, *args, **kwargs):
        carowner = request.user
        print(f"In CarOwnerMyRacesView for carowner: {carowner}")
        participations = RaceParticipant.objects.filter(car_owner= carowner).select_related("race", "car")
        print(f"Races {carowner} in: {participations}")
        
        race_list = {}
        
        for participation in participations:
            race = participation.race
            car = participation.car
            owner = f"{race.owner.name} {race.owner.lastname}"
            
            if race.name not in race_list:
                race_list[race.name] = {
                    "details": {
                        "location": race.location,
                        "date": race.date.strftime("%Y-%m-%d"),
                        "num_cars": race.num_cars,
                        "owner": owner,
                        "id": race.id
                    },
                    "my_cars": [],
                    "other_cars": []
                }
                
                # Get all participants in the race, but exclude the user's car
                other_participants = RaceParticipant.objects.filter(race=race).exclude(car_owner=carowner).select_related("car", "car_owner")
                for participant in other_participants:
                    race_list[race.name]["other_cars"].append({
                        "car_name": participant.car.name,
                        "owner": f"{participant.car_owner.name} {participant.car_owner.lastname}",
                        "username": participant.car_owner.username,
                        "email": participant.car_owner.email,
                    })
            
            race_list[race.name]["my_cars"].append({
                "id": car.id,
                "car_name": car.name
            })
            
        print(race_list)
            
        return Response(race_list)
    
    
class RemoveCarFromRaceView(APIView):
    authentication_classes = [CognitoJWTAuthentication]
    
    def delete(self, request):       
        race_id = request.data.get("race_id")
        car_id = request.data.get("car_id")

        if not race_id or not car_id:
            return Response({"error": "Race ID and Car ID are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        participant = RaceParticipant.objects.filter(race=race_id, car=car_id)
        if participant.exists():
            participant.delete()
            return Response({"message": "Car removed from race successfully."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Car not found in race."}, status=status.HTTP_404_NOT_FOUND)

class SetCarEligibilityView(APIView):
    serializer_class = CarSerializer
    permission_classes = [IsCarOwner]
    
    def post(self, request, *args, **kwargs):
        print("In set eligibility")
        car_id = request.data.get('car_id')
        is_eligible = request.data.get('is_eligible')

        if car_id is None or is_eligible is None:
            return Response({"error": "car_id and is_eligible are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            car = Car.objects.get(id=car_id, owner=request.user)
        except Car.DoesNotExist:
            return Response({"error": "Car not found or you do not have permission."},
                            status=status.HTTP_404_NOT_FOUND)

        # Convert "true"/"false" strings to boolean if necessary
        if isinstance(is_eligible, str):
            is_eligible = is_eligible.lower() == 'true'

        car.is_eligible = is_eligible
        car.save()

        return Response({
            "message": f"Car '{car.name}' eligibility set to {car.is_eligible}."
        }, status=status.HTTP_200_OK)

class ListEligibleCarsView(generics.ListAPIView):
    serializer_class = CarSerializer
    permission_classes = [IsRaceOwner]
    
    def get_queryset(self):
        user = self.request.user
        race_id = self.request.query_params.get("race_id")
        print(f"race id: {race_id} owned by {user}")
        
        # Start with eligible cars
        queryset = Car.objects.filter(is_eligible=True)
        
        if race_id:
            # try:
            #     race = Race.objects.filter(race_id)
            # except Race.DoesNotExist as e:
            #     print(str(e))
            #     return
            
            participants = RaceParticipant.objects.filter(race=race_id).values_list("car", flat=True)
            queryset = queryset.exclude(id__in=participants)
        
        print(queryset)
        return queryset
    

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
