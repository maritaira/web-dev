import os
import boto3
import torch
from torchvision import datasets, transforms, models
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from datetime import datetime
from django.http import JsonResponse
from webapp.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME


# Define your AWS S3 bucket
bucket_name = 'sp4-races-bucket'

# Dummy placeholder; replace with your real function
def get_user_class_pairs(race_id):
    # Should return a list of (username, class_name) tuples
    return [('john', 'camaro'), ('alice', 'supra')]

def download_s3_folder(bucket, prefix, local_dir):
    try:
        # Initialize the S3 client once
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION_NAME)
    except Exception as e:
        print(f"Error initializing S3 client: {e}")
        return

    # List the objects in the S3 bucket with the given prefix
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if 'Contents' in response:
        for obj in response['Contents']:
            if obj['Key'].endswith('/'):
                continue  # Skip directories
            target = os.path.join(local_dir, os.path.relpath(obj['Key'], prefix))
            os.makedirs(os.path.dirname(target), exist_ok=True)

            try:
                # Download the file
                s3.download_file(bucket, obj['Key'], target)
                print(f"Downloaded: {obj['Key']} to {target}")
            except Exception as e:
                print(f"Error downloading {obj['Key']}: {e}")
    else:
        print(f"No objects found in {bucket} with prefix {prefix}")

def upload_file_to_s3(file_path, bucket_name, key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{key}")

def filter_dataset(data_dir, allowed_pairs):
    for split in ['train', 'val']:
        split_dir = os.path.join(data_dir, split)
        if not os.path.isdir(split_dir):
            continue
        for class_dir in os.listdir(split_dir):
            full_class_path = os.path.join(split_dir, class_dir)
            if not os.path.isdir(full_class_path):
                continue
            if not any(class_dir == c and u in full_class_path for u, c in allowed_pairs):
                print(f"Removing disallowed class dir: {full_class_path}")
                # os.system(f'rm -rf "{full_class_path}"')

def train_model(data_dir, save_dir):
    data_transforms = {
        'train': transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
        ]),
        'val': transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ]),
    }

    image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x])
                      for x in ['train', 'val']}

    dataloaders = {x: DataLoader(image_datasets[x], batch_size=32, shuffle=True, num_workers=4)
                   for x in ['train', 'val']}

    model = models.resnet18(pretrained=True)
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, len(image_datasets['train'].classes))

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    best_acc = 0.0
    for epoch in range(25):  # Adjust number of epochs as needed
        print(f"Epoch {epoch + 1}")
        for phase in ['train', 'val']:
            model.train() if phase == 'train' else model.eval()
            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    _, preds = torch.max(outputs, 1)
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / len(image_datasets[phase])
            epoch_acc = running_corrects.double() / len(image_datasets[phase])
            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_path = os.path.join(save_dir, 'best.pt')
                torch.save(model.state_dict(), best_model_path)
                print(f"Saved best model to {best_model_path}")
    metadata_path = os.path.join(save_dir, 'best.pt')


    torch.save({
        'class_to_idx': image_datasets['train'].class_to_idx,
        'input_size': 224,
    }, metadata_path)

    return best_model_path

def main(owner, race_name, race_id):
    dst_prefix = f"{owner}/{race_name}/dataset/"
    allowed_user_class_pairs = get_user_class_pairs(race_id)
    print(f"dst_prefix is: {dst_prefix}")

    local_dataset_path = './ml_integration/dataset'
    save_dir = './ml_integration/model_output'
    os.makedirs(local_dataset_path, exist_ok=True)
    os.makedirs(save_dir, exist_ok=True)

    print(f"Downloading dataset from s3://{bucket_name}/{dst_prefix}")
    download_s3_folder(bucket_name, dst_prefix, local_dataset_path)
    print(f"📁 Dataset downloaded to: {local_dataset_path}")
    print(f"Check if the following directories exist:")
    print(f"- Train directory: {os.path.join(local_dataset_path, 'train')}")
    print(f"- Validation directory: {os.path.join(local_dataset_path, 'val')}")



    if not os.path.isdir(os.path.join(local_dataset_path, 'train')):
        print(f"Error: Missing 'train' directory at {local_dataset_path}/train")
        return JsonResponse({"error": f"Missing 'train' directory at {local_dataset_path}/train"}, status=500)
    
    if not os.path.isdir(os.path.join(local_dataset_path, 'val')):
        print(f"Error: Missing 'val' directory at {local_dataset_path}/val")
        return JsonResponse({"error": f"Missing 'val' directory at {local_dataset_path}/val"}, status=500)


    print("Filtering dataset to include only allowed user-class pairs...")
    filter_dataset(local_dataset_path, allowed_user_class_pairs)

    print("Starting training...")
    weights_path = train_model(local_dataset_path, save_dir)

    print("Uploading trained model and config to S3...")
    upload_file_to_s3(weights_path, bucket_name, f"{owner}/{race_name}/weights/best.pt")

    print("Training complete!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner', type=str, required=True)
    parser.add_argument('--race_name', type=str, required=True)
    parser.add_argument('--race_id', type=str, required=True)
    args = parser.parse_args()

    main(args.owner, args.race_name, args.race_id)


"""
Notes:
- Decaying the learning rate allows for the training to take large steps at first but 
    lowering after a couple of epochs allows the model for finer adjustments and converge
    to a better local minimum without overshooting the optimal solution
- By not decaying the learning rate it will likely overshoot the optimal solution and lead to 
    oscillations. Leads to instability and slower convergence
-Cross Entropy Loss: measures the difference between the predicted probability distribution 
    and the true distribution.
-for scaling, think about saving each weight .pt file for each user and replace based on if they want to keep
    or replace their old saved configurations in a bucket

TODO:
- When training on 1 class, accuracy goes to 1, need negative data/class to set a threshold
"""
