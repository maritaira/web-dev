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
        #username = request.query_params.get("username")
        car_name = request.query_params.get("car_name")
        
        #if not username or not car_name:
        if not car_name:
            return Response({"error": "car_name required."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Image.objects.filter( car_name=car_name)
        # print("filtered images in list()")
        # print(f"Queryset count: {queryset.count()}")  # Debugging
        # for obj in queryset:
        #     print(obj)  # Ensure queryset actually contains objects

        serializer = self.get_serializer(queryset, many=True)
        # print("serializer initialized")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        #username = request.data.get('username')
        car_name = request.data.get('car_name')
        images = request.FILES.getlist('images')
        
        
        if not images:
            return Response({'error': 'No files provided.'}, status=status.HTTP_400_BAD_REQUEST)
        if not car_name:
            return Response({'error': ' car_name required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        uploads = []
        
        try:
            for image in images:
                serializer = self.get_serializer(data={'car_name': car_name, 
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
        print("Checking for new videos in S3 and syncing with MySQL...")

        race_bucket = RacesBucketStorage()
        existing_videos = {video.file.name for video in Video.objects.all()}  # Set of existing video names in MySQL

        all_races = race_bucket.listdir('')[0]  # Get all race directories
        valid_ext = (".mp4", ".mov", ".avi", ".mkv")

        new_videos = []

        for race in all_races:
            subdirectory = f"{race}/"
            files = race_bucket.listdir(subdirectory)[1]  # Get video files inside race directory

            for file in files:
                if file.lower().endswith(valid_ext) and file not in existing_videos:
                    print(f"New video found: {file}")
                    video_obj = Video.objects.create(race=race, file=f"{subdirectory}{file}")
                    new_videos.append(video_obj)

        videos = Video.objects.all()

        video_list = [
            {
                "race": video.race,
                "video_url": video.file.url,  # Ensure proper S3 URL resolution
            }
            for video in videos
        ]

        return Response(video_list, status=status.HTTP_200_OK)

            
        
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

# media/views.py (assuming it's set up for an API)
from rest_framework.response import Response
from rest_framework.decorators import api_view
from media.models import Video

@api_view(['GET'])
def get_videos(request):
    race_name = request.GET.get('race', '')
    
    if race_name:
        videos = Video.objects.filter(race__icontains=race_name)
    else:
        videos = Video.objects.all()

    video_data = []
    for video in videos:
        video_data.append({
            'race': video.race,
            'file': video.file.url
        })

    return Response(video_data)
