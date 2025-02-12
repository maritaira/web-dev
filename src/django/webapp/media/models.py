from django.db import models
from webapp.storages import UsersBucketStorage

# Create your models here.

def image_upload_to(instance, filename):
    path = f"{instance.username}/cars/{instance.car_name}/images/{filename}"
    print(f"Uploading to: {path}")
    return path

class Image(models.Model):
    username = models.CharField(max_length=255, default="default_user")
    car_name = models.CharField(max_length=100)
    image = models.ImageField(storage=UsersBucketStorage, upload_to=image_upload_to) 
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.image.name}"
