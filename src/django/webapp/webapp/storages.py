from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class CarsBucketStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_CARS_BUCKET_NAME


class RacesBucketStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_RACES_BUCKET_NAME
