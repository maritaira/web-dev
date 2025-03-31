from django.db import models
from webapp.storages import CarsBucketStorage, RacesBucketStorage
from django.conf import settings

# Create your models here.

def image_upload_to(instance, filename):
    path = f"{instance.car.owner.username}/{instance.car.name}/images/{filename}"
    print(f"Uploading Image to: {path}")
    return path

class Image(models.Model):
    # username = models.CharField(max_length=255, default="default_user")
    # car_name = models.CharField(max_length=100)
    
    # links image to car (car.images)
    car = models.ForeignKey('races.Car', on_delete=models.CASCADE,  null=True, blank=True, related_name='images')
    image = models.ImageField(storage=CarsBucketStorage, upload_to=image_upload_to) 
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.image.name}"

def video_upload_to(instance, filename):
    path = f"{instance.race.owner.username}/{instance.race.name}/video/{filename}"
    print(f"Uploading Video to: {path}")
    return path

def thumbnail_upload_to(instance, filename):
    path = f"{instance.race}/{filename}"
    print(f"Uploading Thumbnail to: {path}")
    return path

class Video(models.Model):
    # race.videos
    race = models.ForeignKey('races.Race', on_delete=models.CASCADE,  null=True, blank=True, related_name='videos')
    # user.videos
    raceowner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="videos")
    # file = models.FileField(storage=RacesBucketStorage, upload_to=video_upload_to)
    file = models.FileField(storage=RacesBucketStorage(), upload_to=video_upload_to)
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.race
