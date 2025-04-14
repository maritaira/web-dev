import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import torch.backends.cudnn as cudnn
import numpy as np
import torchvision
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt
import time
import os
from PIL import Image
import multiprocessing
import boto3
from webapp.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME
from django.http import JsonResponse
import shutil
# Helper Functions

def download_s3_folder(bucket, prefix, local_dir):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=AWS_REGION_NAME)
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if 'Contents' in response:
        for obj in response['Contents']:
            if obj['Key'].endswith('/'):
                continue
            target = os.path.join(local_dir, os.path.relpath(obj['Key'], prefix))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            s3.download_file(bucket, obj['Key'], target)
            print(f"Downloaded: {obj['Key']} to {target}")

def upload_file_to_s3(file_path, bucket_name, key):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=AWS_REGION_NAME)
    s3.upload_file(file_path, bucket_name, key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{key}")


# Early Stopping

class EarlyStopping:
    def __init__(self, patience=4, verbose=False):
        self.patience = patience
        self.verbose = verbose
        self.best_loss = None
        self.early_stop = False
        self.best_model_params = None
        self.counter = 0

    def __call__(self, val_loss, model):
        if val_loss is None:
            return
        if self.best_loss is None:
            self.best_loss = val_loss
            self.best_model_params = model.state_dict()

        elif val_loss > self.best_loss:
            self.counter += 1
            if self.verbose:
                print(f"EarlyStopping Counter: {self.counter} out of {self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.best_model_params = model.state_dict()
            self.counter = 0

# def imshow(inp, title=None):
#     """Display image for Tensor."""
#     inp = inp.numpy().transpose((1, 2, 0))
#     mean = np.array([0.485, 0.456, 0.406])
#     std = np.array([0.229, 0.224, 0.225])
#     inp = std * inp + mean
#     inp = np.clip(inp, 0, 1)
#     plt.imshow(inp)
#     if title is not None:
#         plt.title(title)
#     plt.pause(0.001)

def train_model(model, criterion, optimizer, scheduler, num_epochs=25, patience=5, save_path='./ml_integration/model_output/best.pt'):
    since = time.time()
    early_stopping = EarlyStopping(patience=patience, verbose=True)
    best_acc = 0.0

    for epoch in range(num_epochs):
        print(f'Epoch {epoch}/{num_epochs - 1}')
        print('-' * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            if phase == 'train':
                scheduler.step()

            if dataset_sizes[phase] == 0:
                print(f"⚠️ No data for {phase} phase. Skipping...")
                continue
            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.float() / dataset_sizes[phase]

            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val':
                if epoch_acc > best_acc:
                    best_acc = epoch_acc
                    torch.save(model.state_dict(), save_path)

                    
                early_stopping(epoch_loss, model)
                if early_stopping.early_stop:
                    print("Stopping Training Early!")
                    time_elapsed = time.time() - since
                    print(f"Training stopped at epoch {epoch} after {time_elapsed//60:.0f}m {time_elapsed%60:.0f}s")
                    model.load_state_dict(torch.load(save_path))
                    return model
        print()

    time_elapsed = time.time() - since
    print(f'Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
    print(f'Best val Acc: {best_acc:4f}')

    model.load_state_dict(torch.load(save_path))
    return model

def visualize_model(model, num_images=6):
    was_training = model.training
    model.eval()
    images_so_far = 0
    fig = plt.figure()

    with torch.no_grad():
        for i, (inputs, labels) in enumerate(dataloaders['val']):
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            for j in range(inputs.size()[0]):
                images_so_far += 1
                ax = plt.subplot(num_images // 2, 2, images_so_far)
                ax.axis('off')
                ax.set_title(f'predicted: {class_names[preds[j]]}')
                # imshow(inputs.cpu().data[j])

                if images_so_far == num_images:
                    model.train(mode=was_training)
                    return
        model.train(mode=was_training)

def main(owner, race_name, race_id, allowed_user_class_pairs):
    cudnn.benchmark = True
    plt.ion()

    bucket_name = 'sp4-races-bucket'
    prefix = f"{owner}/{race_name}/dataset/"  # should end with '/'
    local_dataset_path = './ml_integration/dataset'
    save_dir = './ml_integration/model_output'
    os.makedirs(local_dataset_path, exist_ok=True)
    os.makedirs(save_dir, exist_ok=True)

    print("Downloading data from S3...")
    download_s3_folder(bucket_name, prefix, local_dataset_path)
    print("Download complete.")


    data_dir = local_dataset_path
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if not os.path.isdir(os.path.join(local_dataset_path, 'train')) or not os.path.isdir(os.path.join(local_dataset_path, 'val')):
        return JsonResponse({"error": "Missing 'train' or 'val' directory"}, status=500)

    print("Starting training...")
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    global image_datasets, dataloaders, dataset_sizes, class_names, device

    image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x),
                                              data_transforms[x])
                      for x in ['train', 'val']}
    dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x],
                                                  batch_size=2,
                                                  shuffle=True,
                                                  num_workers=4)
                   for x in ['train', 'val']}
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
    class_names = image_datasets['train'].classes

    device = torch.device("cpu")
    print(device)

    inputs, classes = next(iter(dataloaders['train']))
    out = torchvision.utils.make_grid(inputs)
    # imshow(out, title=[class_names[x] for x in classes])

    model_conv = torchvision.models.resnet18(weights='IMAGENET1K_V1')
    for param in model_conv.parameters():
        param.requires_grad = False

    num_ftrs = model_conv.fc.in_features
    model_conv.fc = nn.Linear(num_ftrs, len(class_names))
    model_conv = model_conv.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer_conv = optim.SGD(model_conv.fc.parameters(), lr=0.001, momentum=0.9)
    exp_lr_scheduler = lr_scheduler.StepLR(optimizer_conv, step_size=7, gamma=0.1)

    ##save_path = './ml_integration/model_output/best.pt'
    model_conv = train_model(model_conv, criterion, optimizer_conv,
                             exp_lr_scheduler, num_epochs=25)

    print("Uploading trained model...")
    save_path = './ml_integration/model_output/best.pt'
    #MIGHT CAUSE ISSUES
    os.makedirs(save_dir, exist_ok=True)

    
    upload_file_to_s3(save_path, bucket_name, f"{owner}/{race_name}/model/best.pt")

    dataset_dir = os.path.join('ml_integration', 'dataset')
    model_output_dir = os.path.join('ml_integration', 'model_output')

    # Delete folders if they exist
    for folder in [dataset_dir, model_output_dir]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"Deleted local folder: {folder}")
        else:
            print(f"Folder not found (already deleted?): {folder}")


if __name__ == '__main__':
    main()

