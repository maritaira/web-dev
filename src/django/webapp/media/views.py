from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.core.files import File
from .models import Image, Video
from .serializers import ImageSerializer, VideoSerializer
from webapp.storages import RacesBucketStorage
from rest_framework.decorators import api_view

# Image ViewSet
class ImageViewSet(ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def list(self, request):
        car_name = request.query_params.get("car_name")
        if not car_name:
            return Response({"error": "car_name required."}, status=status.HTTP_400_BAD_REQUEST)
        queryset = Image.objects.filter(car_name=car_name)
        serializer = self.get_serializer(queryset, many=True)
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
                self.perform_create(serializer)
                uploads.append(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(uploads, status=status.HTTP_201_CREATED)

# Video ViewSet
class VideoViewSet(ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    parser_classes = (MultiPartParser, FormParser)

    def sync_videos_from_s3(self):
        print("Syncing videos from S3...")  # Add this to confirm syncing starts
        race_bucket = RacesBucketStorage()
        
        # Fetch all existing video paths from the DB (using a unique path or key)
        existing_video_paths = {video.file.name for video in Video.objects.all()}  # Use the actual file path for comparison
        
        valid_ext = (".mp4", ".mov", ".avi", ".mkv")  # Supported video extensions
        all_races = race_bucket.listdir('')[0]  # This should list all races in the root directory of your S3 bucket
        print(f"All races in S3: {all_races}")

        new_videos = []
        for race in all_races:
            subdirectory = f"{race}/"
            files = race_bucket.listdir(subdirectory)[1]  # Get list of files in the subdirectory

            for file in files:
                file_path = f"{subdirectory}{file}"

                if file.lower().endswith(valid_ext) and file_path not in existing_video_paths:
                    # New video found; create a new Video object in DB
                    print(f"New video found: {file}")
                    new_video = Video.objects.create(race=race, file=file_path)
                    existing_video_paths.add(file_path)  # Add to the set of existing video paths
                    new_videos.append(new_video)
        
        return new_videos



    # def list(self, request):
    #     print(f"Sync query parameter: {request.GET.get('sync')}")

    #     if request.GET.get("sync"):  # Only sync when manually triggered
    #         print("Checking for new videos in S3 and syncing with MySQL...")
    #         self.sync_videos_from_s3()
    #         print("getting here")

    #     print("list is starting here")
    #     videos = Video.objects.all()
    #     video_list = [{"race": video.race, "video_url": video.file.url} for video in videos]
    #     return Response(video_list, status=status.HTTP_200_OK)

    def list(self, request):
        print("list is starting here")

        # Check if sync query parameter exists, if not sync by default
        if request.GET.get("sync", None):
            print("Syncing videos from S3...")
            self.sync_videos_from_s3()

        # Fetch existing race titles from the database
        existing_race_titles = {video.race for video in Video.objects.all()}

        # Sync videos from S3
        race_bucket = RacesBucketStorage()
        valid_ext = (".mp4", ".mov", ".avi", ".mkv")  # Supported video extensions
        all_races = race_bucket.listdir('')[0]  # List all races in the root directory of your S3 bucket
        print(f"All races in S3: {all_races}")

        new_videos = []
        for race in all_races:
            if race not in existing_race_titles:  # Check if race title already exists in the DB
                subdirectory = f"{race}/"
                files = race_bucket.listdir(subdirectory)[1]  # Get list of files in the subdirectory

                # Find a video file in the subdirectory
                video_file = next((f for f in files if f.lower().endswith(valid_ext)), None)
                
                if video_file:
                    file_path = f"{subdirectory}{video_file}"

                    # Create video entry in the database if not found
                    print(f"New video found for race: {race}")
                    new_video = Video.objects.create(race=race, file=file_path)
                    new_videos.append(new_video)

        # After checking and creating new videos, get all videos in the database
        videos = Video.objects.all()
        video_list = [{"race": video.race, "video_url": video.file.url} for video in videos]
        
        return Response(video_list, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        race = request.data.get('race')
        if not race:
            return Response({'error': 'race name required'}, status=status.HTTP_400_BAD_REQUEST)
        
        race_bucket = RacesBucketStorage()
        subdirectory = f"{race}/"
        
        # Check S3 for videos
        files = race_bucket.listdir(subdirectory)[1]
        valid_ext = (".mp4", ".mov", ".avi", ".mkv")
        video_file = next((f for f in files if f.lower().endswith(valid_ext)), None)
    
        if not video_file:
            return Response({"error": "No valid video file found"}, status=status.HTTP_404_NOT_FOUND)
        
        path = f"{subdirectory}{video_file}"
        full_path = race_bucket.url(path)
        
        try:
            video = race_bucket.open(path)  # Fetch the file from S3
        except Exception as e:
            return Response({"error": f"Error fetching video file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
        # Create video object and save it to the database
        serializer = self.get_serializer(data={'race': race, 'file': File(video, name=video_file)})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save video to DB
        self.perform_create(serializer)
        
        # Video created and saved, now return the data
        return Response(serializer.data, status=status.HTTP_201_CREATED)

#API Endpoints
    @api_view(['POST'])
    def sync_videos(request):
        print("Manually syncing videos from S3...")
        viewset = VideoViewSet()
        new_videos = viewset.sync_videos_from_s3()
        return Response({"message": f"Synced {len(new_videos)} new videos."})

    @api_view(['GET'])
    def get_videos(request):
        race_name = request.GET.get('race', '')
        videos = Video.objects.filter(race__icontains=race_name) if race_name else Video.objects.all()
        video_data = [{'race': video.race, 'file': video.file.url} for video in videos]
        return Response(video_data)
