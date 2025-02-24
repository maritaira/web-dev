from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class UsersBucketStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_USERS_BUCKET_NAME
    
    def __init__(self, *args, **kwargs):
        print(f"UsersBucketStorage is using bucket: {self.bucket_name}")
        super().__init__(*args, **kwargs)
        
        
class RacesBucketStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_RACES_BUCKET_NAME
    
    def __init__(self, *args, **kwargs):
        print(f"RacesBucketStorage is using bucket: {self.bucket_name}")
        super().__init__(*args, **kwargs)
        