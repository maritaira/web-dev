from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.core.files import File
from .models import Image, Video
from .serializers import ImageSerializer, VideoSerializer
from webapp.storages import RacesBucketStorage
# from django.conf import settings

# Create your views here.
class ImageViewSet(ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    
    def list(self, request):
        # print("GET request received")
        username = request.query_params.get("username")
        car_name = request.query_params.get("car_name")
        
        if not username or not car_name:
            return Response({"error": "username and car_name are required."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Image.objects.filter(username=username, car_name=car_name)
        # print("filtered images in list()")
        # print(f"Queryset count: {queryset.count()}")  # Debugging
        # for obj in queryset:
        #     print(obj)  # Ensure queryset actually contains objects

        serializer = self.get_serializer(queryset, many=True)
        # print("serializer initialized")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        car = request.data.get('car')
        images = request.FILES.getlist('images')
        
        
        if not images:
            return Response({'error': 'No files provided.'}, status=status.HTTP_400_BAD_REQUEST)
        if not car:
            return Response({'error': 'Car required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        uploads = []
        
        try:
            for image in images:
                serializer = self.get_serializer(data={'car': car,
                                                       'image': image
                                                       })
                
                serializer.is_valid(raise_exception=True)
                # print("passed isvalid serializer")
                self.perform_create(serializer)
                # print(f"Serializer.data: {serializer.data}")
                uploads.append(serializer.data)
                print(f"Successfully added {image.name}")
                
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return Response(
                {"detail": {str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(uploads, status=status.HTTP_201_CREATED)
    
    
class VideoViewSet(ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def list(self, request):
        print("VIDEO GET request received")
        race_name = request.query_params.get("race")
        print(race_name)
        
        if not race_name:
            return Response({"error": "Race name required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            video = Video.objects.get(race=race_name)
            print(video.file.url)
        
            return Response({"race": video.race,
                             "video_url": video.file.url})
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return Response(
                {"detail": {str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # serializer = self.get_serializer(instance)
        # print("serializer initialized")
        
        # return Response(serializer.data, status=status.HTTP_200_OK)
        
        
    def create(self, request, *args, **kwargs):
        race = request.data.get('race')
        
        if not race:
            return Response({'error': 'race name required'}, status=status.HTTP_400_BAD_REQUEST)
        
        race_bucket = RacesBucketStorage()
        subdirectory = f"{race}/"
        files = race_bucket.listdir(subdirectory)[1]
        
        valid_ext = (".mp4", ".mov", ".avi", ".mkv")
        video_file = next((f for f in files if f.lower().endswith(valid_ext)), None)
    
        if not video_file:
            return Response({"error": "No valid video file found"}, status=status.HTTP_404_NOT_FOUND)
        print(f"received video_file: {video_file}")
        
        path = f"{subdirectory}{video_file}"
        full_path = race_bucket.url(path)
        print(full_path)

        try:
            video = race_bucket.open(path)  # Fetch the file from S3
        except Exception as e:
            return Response({"error": f"Error fetching video file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
        print("retrieved video")
    
        serializer = self.get_serializer(data={'race': race,  
                                                'file': File(video, name=video_file)
                                                })
                
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            print(f"Validation Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
