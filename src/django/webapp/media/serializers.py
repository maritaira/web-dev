# upload/serializers.py
from rest_framework import serializers
from django.core.files.storage import default_storage
from .models import Image

class ImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Image
        fields = ['username', 'car_name', 'image', 'image_url', 'upload_time']
        
    def get_image_url(self, obj):
        # print(f"image path: {obj.image.name}")
        return default_storage.url(obj.image.name)