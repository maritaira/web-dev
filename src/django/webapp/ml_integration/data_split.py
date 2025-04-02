import boto3
import random
import os
from urllib.parse import urlparse
from webapp.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME

def split_dataset_s3(source_bucket_name, dest_bucket_name, source_prefix, dest_prefix, allowed_user_class_pairs=None, split_ratio=0.8):
    """
    Splits an image dataset stored in S3 into training and validation sets.

    Args:
        source_bucket_name (str): The name of the source S3 bucket.
        dest_bucket_name (str): The name of the destination S3 bucket.
        source_prefix (str): The S3 prefix where the dataset is stored (e.g., "").
        dest_prefix (str): The S3 prefix where training data will be stored (e.g., "username/racename/dataset/").
        split_ratio (float): Fraction of data to use for training (default 0.8 for 80% training, 20% validation).
        allowed_user_class_pairs (set): Set of allowed (username, class_name) pairs to include in the dataset.
    """
    if not allowed_user_class_pairs:
        print("You must filter the user-car pairs that you want to use in training")
    
     # Initialize S3 client (Assumes AWS credentials are configured)
    try:
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION_NAME)
    except Exception as e:
        print(f"Error initializing S3 client: {e}")
        return

    # List all objects under the source prefix
    response = s3.list_objects_v2(Bucket=source_bucket_name, Prefix=source_prefix)
    if 'Contents' not in response:
        print("No files found in the source directory.")
        return

    # Organize images by class (assuming class folders inside the source prefix)
    class_files = {}
    for obj in response['Contents']:
        file_key = obj['Key']
        
        # Skip directories
        if file_key.endswith('/'):
            continue
        
        # Extract <username>, <class>, and <filename> from filepath
        parts = file_key[len(source_prefix):].split('/')
        if len(parts) < 3 or parts[2] != "images":
            print(f"Skipping unexpected structure: {file_key}")
            continue
        
        username, class_name, filename = parts[0], parts[1], '/'.join(parts[3:])  # Handle potential subdirs
        
        print(f"Username: {username}")
        print(f"classname: {class_name}")
        print(f"filename: {filename}")
        
        # Skip files if the (username, class_name) pair is not in the allowed list
        if allowed_user_class_pairs and (username, class_name) not in allowed_user_class_pairs:
            continue
        
        unique_class_folder = f"{class_name}_{username}"  # Format new folder name
        
        if unique_class_folder not in class_files:
            print(f"Creating new class folder {unique_class_folder}")
            class_files[unique_class_folder] = []
        
        class_files[unique_class_folder].append(file_key)

    # Process each class
    for unique_class_folder, files in class_files.items():
        random.shuffle(files)  # Shuffle for randomness

        # Determine split index
        split_index = int(len(files) * split_ratio)
        train_files = files[:split_index]
        val_files = files[split_index:]

        # Copy files to train and val directories in S3
        for file_key in train_files:
            filename = file_key.split('/')[-1]  # Extract filename only
            new_key = f"{dest_prefix}train/{unique_class_folder}/{filename}"
            s3.copy_object(Bucket=dest_bucket_name, CopySource={'Bucket': source_bucket_name, 'Key': file_key}, Key=new_key)

        for file_key in val_files:
            filename = file_key.split('/')[-1]  # Extract filename only
            new_key = f"{dest_prefix}val/{unique_class_folder}/{filename}"
            s3.copy_object(Bucket=dest_bucket_name, CopySource={'Bucket': source_bucket_name, 'Key': file_key}, Key=new_key)

        print(f"Class '{unique_class_folder}' split: {len(train_files)} for training, {len(val_files)} for validation.")

if __name__ == "__main__":
    # S3 bucket name and dataset prefixes
    # FOR TESTING THE SCRIPT ITSELF, do not use with ml_integration app
    source_bucket_name = "sp4-cars-bucket"
    dest_bucket_name = "sp4-races-bucket"
    source_prefix = ""
    dest_prefix = "raceowner/race 1/dataset/"
    allowed_user_class_pairs = {("carowner", "car1"), ("testuser", "mazda"), ("testuser","audi")}

    # Split dataset in S3
    split_dataset_s3(source_bucket_name, dest_bucket_name, source_prefix, dest_prefix, allowed_user_class_pairs)
