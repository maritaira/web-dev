import boto3
import os

''' NEED TO CHANGE FUNCTIONALITY BASED ON WHERE/HOW TO CONFIGURE S3 CREDENTIALS'''

def download_s3_files(username, racename, download_path):
    # Retrieve bucket name from environment variable
    bucket_name = os.getenv("S3_RACES_BUCKET_NAME")
    if not bucket_name:
        print("Error: S3+RACES_BUCKET_NAME environment variable is not set.")
        return
    
     # Initialize S3 client (Assumes AWS credentials are configured)
    try:
        s3 = boto3.client('s3')
    except Exception as e:
        print(f"Error initializing S3 client: {e}")
        return
    
    config_key = f"{username}/{racename}/config/"
    weights_key = f"{username}/{racename}/weights/"
    
    # List objects in the config directory
    config_objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=config_key)
    weights_objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=weights_key)
    
    if 'Contents' in config_objects:
        for obj in config_objects['Contents']:
            if obj['Key'].endswith('.yaml'):
                config_filename = os.path.basename(obj['Key'])
                config_filepath = os.path.join(download_path, config_filename)
                s3.download_file(bucket_name, obj['Key'], config_filepath)
                print(f"Downloaded config file: {config_filepath}")
                break  # Only one config file expected
    else:
        print("No config file found in S3.")
    
    if 'Contents' in weights_objects:
        for obj in weights_objects['Contents']:
            if obj['Key'].endswith('best.pt'):
                weights_filepath = os.path.join(download_path, 'best.pt')
                s3.download_file(bucket_name, obj['Key'], weights_filepath)
                print(f"Downloaded weights file: {weights_filepath}")
                break  # Only one weights file expected
    else:
        print("No weights file found in S3.")

if __name__ == "__main__":
    username = input("Enter username: ")
    racename = input("Enter race name: ")
    download_path = os.path.expanduser("~/Documents/weights")  # Replace with desired download path
    
    os.makedirs(download_path, exist_ok=True)
    download_s3_files(username, racename, download_path)
