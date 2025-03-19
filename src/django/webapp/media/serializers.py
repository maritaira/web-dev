# upload/serializers.py
from rest_framework import serializers
from django.core.files.storage import default_storage
from .models import Image, Video

class ImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Image
        fields = [ 'car_name', 'image', 'image_url', 'upload_time']
        
    def get_image_url(self, obj):
        print(f"image path: {obj.image.name}")
        print(default_storage.url(obj.image.name))
        return default_storage.url(obj.image.name)
    
    
class VideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['race', 'video_url']

    def get_video_url(self, obj):
        # Ensure the URL is properly constructed
        video_url = obj.file  # Assuming the 'file' field stores the URL
        # Decode it once, if it's URL-encoded
        return video_url  # No extra encoding needed here
        