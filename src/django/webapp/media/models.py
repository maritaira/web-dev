from django.db import models
from webapp.storages import CarsBucketStorage, RacesBucketStorage

# Create your models here.

def image_upload_to(instance, filename):
    path = f"{instance.car.owner.username}/{instance.car.name}/images/{filename}"
    print(f"Uploading Image to: {path}")
    return path

class Image(models.Model):   
    # links image to car (car.images)
    car = models.ForeignKey('races.Car', on_delete=models.CASCADE,  null=True, blank=True, related_name='images')
    image = models.ImageField(upload_to=image_upload_to, storage=None) 
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
    # links video to race (race.videos)
    race = models.ForeignKey('races.Race', on_delete=models.CASCADE,  null=True, blank=True, related_name='videos')
    # title  = models.CharField(max_length=255)
    file = models.FileField(upload_to=video_upload_to, storage=None)
    # thumbnail = models.ImageField(storage=RacesBucketStorage, upload_to=thumbnail_upload_to, blank=True, null=True)
    upload_time = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.race.name                          

