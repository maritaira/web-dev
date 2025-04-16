# import yaml
# import uuid
# import sys
# import json
# import boto3
# import os
# from webapp.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME, AWS_STORAGE_RACES_BUCKET_NAME

# # yamlGen.py

# def generateYam(race_id, owner, race_name, num_cars, classes):
#     try:
#         data = {
#             "race_id": race_id,
#             "num_classes": num_cars,
#             "classes": classes
#         }

#         filename = f"config_{race_id}_{uuid.uuid4().hex[:8]}.yaml"
#         local_file_path = f"/tmp/{filename}"
#         with open(local_file_path, "w") as file:
#             yaml.dump(data, file, default_flow_style=False)

#         print(f"📝 Configuration saved locally as {local_file_path}")

#         bucket_name = AWS_STORAGE_RACES_BUCKET_NAME
#         s3_key = f"{owner}/{race_name}/config/{filename}"
#         upload_file_to_s3(local_file_path, bucket_name, s3_key)

#     except Exception as e:
#         print(f"Error: {e}", file=sys.stderr)
#         raise  # Let Django catch and log this

# def upload_file_to_s3(file_path, bucket_name, key):
#     s3 = boto3.client('s3')
#     s3.upload_file(file_path, bucket_name, key)
#     print(f"Uploaded {file_path} to s3://{bucket_name}/{key}")

# def main():
#     try:
#         input_data = json.loads(sys.stdin.read())
#         generateYam(
#             race_id=input_data["race_id"],
#             owner=input_data["owner"],
#             race_name=input_data["race_name"],
#             num_cars=input_data["num_classes"],
#             classes=input_data["classes"]
#         )
#     except Exception as e:
#         print(f"Error: {e}", file=sys.stderr)
#         sys.exit(1)

import yaml
import uuid
import sys
import json
import boto3
import os
from webapp.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION_NAME,
    AWS_STORAGE_RACES_BUCKET_NAME,
)


def generateYam(race_id, owner, race_name, full_name, car_labels):
    try:
        # Construct classes from labels
        classes = [{"id": i + 1, "label": label} for i, label in enumerate(car_labels)]

        data = {
            "user": {"full_name": full_name},
            "num_classes": len(classes),
            "classes": classes
        }

        filename = "config.yaml"
        local_file_path = f"/tmp/{filename}"
        with open(local_file_path, "w") as file:
            yaml.dump(data, file, default_flow_style=False)

        print(f"📝 Configuration saved locally as {local_file_path}")

        s3_key = f"{owner}/{race_name}/config/{filename}"
        upload_file_to_s3(local_file_path, AWS_STORAGE_RACES_BUCKET_NAME, s3_key)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise  # Let Django log this


def upload_file_to_s3(file_path, bucket_name, key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{key}")

def main():
    try:
        input_data = json.loads(sys.stdin.read())
        generateYam(
            race_id=input_data["race_id"],
            owner=input_data["owner"],
            race_name=input_data["race_name"],
            full_name=input_data["full_name"],
            car_labels=input_data["classes"]
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
