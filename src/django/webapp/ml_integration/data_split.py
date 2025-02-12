import boto3
import random
import os
from urllib.parse import urlparse

def split_dataset_s3(bucket_name, source_prefix, train_prefix, val_prefix, split_ratio=0.8):
    """
    Splits an image dataset stored in S3 into training and validation sets.

    Args:
        bucket_name (str): The name of the S3 bucket.
        source_prefix (str): The S3 prefix where the dataset is stored (e.g., "dataset/vehicle_images_vault/").
        train_prefix (str): The S3 prefix where training data will be stored (e.g., "dataset/train/").
        val_prefix (str): The S3 prefix where validation data will be stored (e.g., "dataset/val/").
        split_ratio (float): Fraction of data to use for training (default 0.8 for 80% training, 20% validation).
    """
    s3 = boto3.client('s3')

    # List all objects under the source prefix
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=source_prefix)
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
        
        # Extract class name from the file path (e.g., "dataset/vehicle_images_vault/class1/image.jpg")
        class_name = file_key[len(source_prefix):].split('/')[0]
        
        if class_name not in class_files:
            class_files[class_name] = []
        
        class_files[class_name].append(file_key)

    # Process each class
    for class_name, files in class_files.items():
        random.shuffle(files)  # Shuffle for randomness

        # Determine split index
        split_index = int(len(files) * split_ratio)
        train_files = files[:split_index]
        val_files = files[split_index:]

        # Copy files to train and val directories in S3
        for file_key in train_files:
            new_key = file_key.replace(source_prefix, train_prefix, 1)
            s3.copy_object(Bucket=bucket_name, CopySource={'Bucket': bucket_name, 'Key': file_key}, Key=new_key)

        for file_key in val_files:
            new_key = file_key.replace(source_prefix, val_prefix, 1)
            s3.copy_object(Bucket=bucket_name, CopySource={'Bucket': bucket_name, 'Key': file_key}, Key=new_key)

        print(f"Class '{class_name}' split: {len(train_files)} for training, {len(val_files)} for validation.")

if __name__ == "__main__":
    # S3 bucket name and dataset prefixes
    bucket_name = "seniordesignbucket"
    source_prefix = "vehicle_images_vault/"
    train_prefix = "train/"
    val_prefix = "val/"

    # Split dataset in S3
    split_dataset_s3(bucket_name, source_prefix, train_prefix, val_prefix)
