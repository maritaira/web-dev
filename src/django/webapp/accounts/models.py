from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class CognitoUser(AbstractUser):
    sub = models.UUIDField(unique=True, primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    name = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    groups = models.JSONField(default=list)
    cognito_identity_id = models.CharField(max_length=255, blank=True, null=True)
    
    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username