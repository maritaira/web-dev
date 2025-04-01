import boto3
import os

''' NEED TO CHANGE FUNCTIONALITY BASED ON WHERE/HOW TO CONFIGURE S3 CREDENTIALS'''

def upload_video_to_s3(username, racename, video_path):
    """Uploads a video file to the specified S3 bucket under <username>/<racename>/video/."""
    # Validate video file
    if not os.path.isfile(video_path):
        print(f"Error: File '{video_path}' not found.")
        return
    
    # Extract the filename from the path
    video_filename = os.path.basename(video_path)
    
    # Check file extension
    valid_extensions = (".mp4", ".mov", ".avi", ".mkv")
    if not video_filename.lower().endswith(valid_extensions):
        print("Error: Invalid file format. Allowed formats: .mp4, .mov, .avi, .mkv")
        return
    
    # Construct the S3 key (path in S3 bucket)
    s3_key = f"{username}/{racename}/video/{video_filename}"
    
    # Retrieve bucket name from environment variable
    bucket_name = os.getenv("S3_RACES_BUCKET_NAME")
    if not bucket_name:
        print("Error: S3_RACES_BUCKET_NAME environment variable is not set.")
        return
    
    # Initialize S3 client (Assumes AWS credentials are configured)
    try:
        s3 = boto3.client('s3')
    except Exception as e:
        print(f"Error initializing S3 client: {e}")
        return
    
    try:
        # Upload the video
        s3.upload_file(video_path, bucket_name, s3_key)
        print(f"Upload successful: s3://{bucket_name}/{s3_key}")
    except Exception as e:
        print(f"Upload failed: {e}")

# Example usage
if __name__ == "__main__":
    username = input("Enter username: ")
    racename = input("Enter racename: ")
    video_path = input("Enter path to video file: ")
    
    upload_video_to_s3(username, racename, video_path)