# upload/serializers.py
from rest_framework import serializers
from .models import Image

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['username', 'car_name', 'image', 'upload_time']