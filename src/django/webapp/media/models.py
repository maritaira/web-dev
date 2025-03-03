from django.db import models
from webapp.storages import UsersBucketStorage, RacesBucketStorage

# Create your models here.

def image_upload_to(instance, filename):
    path = f"{instance.car_name}/images/{filename}"
    print(f"Uploading Image to: {path}")
    return path

class Image(models.Model):
    username = models.CharField(max_length=255, default="default_user")
    car_name = models.CharField(max_length=100)
    image = models.ImageField(storage=UsersBucketStorage, upload_to=image_upload_to) 
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.image.name}"
    
def video_upload_to(instance, filename):
    path = f"{instance.race}/{filename}"
    print(f"Uploading Video to: {path}")
    return path

def thumbnail_upload_to(instance, filename):
    path = f"{instance.race}/{filename}"
    print(f"Uploading Thumbnail to: {path}")
    return path

class Video(models.Model):
    # username = models.CharField(max_length=255, default="default_user")
    race = models.CharField(max_length=255)
    # title  = models.CharField(max_length=255)
    file = models.FileField(storage=RacesBucketStorage, upload_to=video_upload_to)
    # thumbnail = models.ImageField(storage=RacesBucketStorage, upload_to=thumbnail_upload_to, blank=True, null=True)
    upload_time = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.race

