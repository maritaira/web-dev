from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
from accounts.cognito_utils import get_s3_client


class CarsBucketStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_CARS_BUCKET_NAME
    
    def __init__(self, *args, **kwargs):
        print(f"Initializing CarsBucketStorage for bucket {self.bucket_name}")
        super().__init__(*args, **kwargs)
        
    def _get_client(self, identity_id, id_token):
        """Return the user-specific S3 client."""
        self.s3_client = get_s3_client(identity_id, id_token)
        return self.s3_client
        
        
class RacesBucketStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_RACES_BUCKET_NAME
    
    def __init__(self, user, *args, **kwargs):
        print(f"Initializing RacesBucketStorage for user: {user.username}")
        # user = kwargs.pop('user', None)
        if not user:
            raise ValueError("User is required to initialize RacesBucketStorage.")
        
        self.s3_client = get_s3_client(user.cognito_identity_id)
        super().__init__(user=user, *args, **kwargs)
        
    def _get_client(self):
        """Return the user-specific S3 client."""
        return self.s3_client
        