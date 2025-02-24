# upload/serializers.py
from rest_framework import serializers
from django.core.files.storage import default_storage
from .models import Image, Video

class ImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Image
        fields = ['username', 'car_name', 'image', 'image_url', 'upload_time']
        
    def get_image_url(self, obj):
        print(f"image path: {obj.image.name}")
        print(default_storage.url(obj.image.name))
        return default_storage.url(obj.image.name)
    
    
class VideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    class Meta:
        model = Video
        # fields = ['username', 'race', 'title', 'file', "video_url", "thumbnail", 'upload_time']
        fields = ['race', 'file', 'video_url', 'upload_time']
        
    def get_video_url(self, obj):
        print(f"video path: {obj.file.url}")
        if obj.file:
            return obj.file.url
        return None
        # return default_storage.url(obj.file.name)
        