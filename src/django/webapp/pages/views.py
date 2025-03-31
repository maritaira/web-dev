from django.shortcuts import render, redirect
from .forms import ImageUploadForm
# Create your views here.
from django.http import HttpResponse, JsonResponse
import requests
from media.models import Video, Image
from races.models import Car, Race
import requests
import boto3
from accounts.middlewares import get_cognito_user
from django.contrib.auth.decorators import login_required
from webapp import settings
from django import template
from races.views import RaceOwnerMyRacesView



#S3_CAR_BUCKET= settings.AWS_STORAGE_CARS_BUCKET_NAME
s3_client=boto3.client("s3")

def index(request):
    return HttpResponse("Hello, world. You're at the pages view.")

def dashboard(request):
    image = None
    if request.method == 'POST' and request.FILES.get('image'):
        # Handle the image upload
        username = request.POST.get('username')
        car_name = request.POST.get('car_name')
        image_file = request.FILES['image']
        
        # Save the image instance
        image = Image.objects.create(
            username=username,
            car_name=car_name,
            image=image_file
        )

        # Redirect to the dashboard or show a success message
        return redirect('pages:dashboard')  # You can change this based on your flow

    # Pass the image context to the template
    user_groups = request.session.get('user_groups', [])
    return render(request, 'dashboard.html', {'image': image, 'user_groups': user_groups})


def carowner_videos(request):
    videos = Video.objects.all()
    context = {
        'videos': videos
    }

    return render(request, 'carowner_videos.html', context)

def raceowner_videos(request):
    videos = Video.objects.all()
    context = {
        'videos': videos
    }

    return render(request, 'raceowner_videos.html', context)



def login_pg(request):
    return render(request, 'login.html')

def create_acc(request):
    return render(request, 'create_acc.html')

def create_race(request):
    # permission = IsRaceOwner()
    # if permission.has_permission(request, None):
    #     return render(request, 'create_race.html')
    
    # return redirect('index')
    return render(request, 'create_race.html')

def new_car(request):
    return render(request, 'new_car.html')




MEDIA_API_URL = "http://127.0.0.1:8000/media/"

def play_video(request):
    next = request.GET.get('next')
    race_id = request.GET.get('race')
    
    race = Race.objects.filter(id=race_id).first()
    # Fetch the video corresponding to the race title from the database
    video = Video.objects.filter(race=race).first()
    # video_url = request.GET.get('video_url')
    # video = Video.objects.filter(video_url=video_url)

    if not video:
        return render(request, 'play_video.html', {'error': "Video not found."})

    # Pass video URL to the template for rendering
    video_url = video.file.url

    return render(request, 'play_video.html', {'race_title': video.race.name, 'video_url': video_url, 'next': next})


def display_images(request):
    """Fetch images for all cars or a specific car"""
    images = []
    car_list = []
    car_name = request.GET.get("car_name", "")
    fetch_all_images_url = f"{MEDIA_API_URL}images/?car_name={car_name}"

    try:
        response = requests.get(fetch_all_images_url)
        if response.status_code == 200:
            all_images = response.json()  # Should be a list of image objects
            car_list = list(set(img["car_name"] for img in all_images))  # Extract unique car names
            response_data = response.json()
            if "images" in response_data:
                all_images = response_data["images"]  # Extract the image list
                print("Fetched Images:", images)
            else:
                print("Unexpected API response:", response_data)

            # If a specific car is selected, filter images
            if car_name:
                images = [img for img in all_images if img["car_name"] == car_name]
            else:
                images = all_images
        else:
            return render(request, "image_upload.html", {"error": "Could not retrieve images."})
            
    except requests.exceptions.RequestException as e:
        return render(request, "image_upload.html", {"error": f"Error retrieving images: {str(e)}"})

    print("API Response:", all_images)
 
    return render(request, "image_upload.html", {
        "images": images,
        "car_list": car_list,
        "car_name": car_name
    })


def upload_image(request):
    if request.method == "POST":
        username = request.POST.get("username")
        car_name = request.POST.get("car_name")
        images = request.FILES.getlist("images")
        
        # print(username)
        # print(car_name)
        
        if not username or not car_name:
            return render(request, "image_upload.html", {"error": "Username and Car Name are required."})

        if not images:
            return render(request, "image_upload.html", {"error": "No images were selected."})
        
        
        files = [("images", (img.name, img, img.content_type)) for img in images]
        data = {"username": username, "car_name": car_name}
        # print(files)
        # print(MEDIA_API_URL)
        try:
            # print("sending request to backend")
            response = requests.post(
                MEDIA_API_URL,
                data=data,
                files=files
            )
            # print(f"Response Status: {response.status_code}")
            # print(f"Response Content: {response.text}")
            
            if response.status_code == 201:
                uploaded_images = response.json()
                # print("successfully uploaded images from frontend")
                return render(request, "image_upload.html", {"success": "Images uploaded successfully!", "images": uploaded_images})
            else:
                # print("failed uploading images from frontend")
                return render(request, "image_upload.html", {"error": "Upload failed: " + response.text})
        except requests.exceptions.RequestException as e:
            # print("exception")
            return render(request, "image_upload.html", {"error": f"Error connecting to backend: {str(e)}"})
    # print("default return line")
    return render(request, "image_upload.html")

def get_s3_images(username):
    s3 = boto3.client('s3')
    bucket_name = settings.AWS_STORAGE_CARS_BUCKET_NAME
    prefix = f'cars/{username}/'  # Assuming the images are stored under the username folder
    
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        images = []
        
        for obj in response.get('Contents', []):
            images.append(obj['Key'])  # This returns the file key for each image
        
        return images
    except NoCredentialsError:
        return None

# def all_cars_view(request):
#     # Retrieve the username from the session
#     username = request.session.get('username')
#     if not username:
#         return JsonResponse({"error": "User not authenticated"}, status=401)
    
#     # Use the username to get the images from S3
#     images = get_s3_images(username)
    
#     if images is None:
#         return JsonResponse({"error": "Could not retrieve images from S3"}, status=500)
    
#     # Assuming the images are URLs or S3 paths that can be directly used
#     # Prepare the context to render in the template
#     context = {
#         'username': username,
#         'images': images
#     }

#     # Render your template with the images data
#     return render(request, 'all_cars.html', context)

   # Custom filter functi
def all_cars(request):
    username = request.session.get('username')
    cars = Car.objects.filter(owner__username=username)

    # Get images for each car
    car_images = {}
    print(car_images)
    for car in cars:
        images = Image.objects.filter(car=car)
        print(car_images)

        #car_images[car.name] = car.images.all()
        car_images[car.name] = [image.image.url for image in images]  # Storing the image URLs

        print(car_images[car.name])


    return render(request, 'all_cars.html', {'username': username, 'cars': cars, 'car_images': car_images})

def raceDash(request):
    # view = RaceOwnerMyRacesView.as_view()
    
    # # Call the view method to get the response data
    # response = view(request)
    
    # # Check if the response is JSON and return it to the template
    # if isinstance(response, JsonResponse):
    #     race_data = response.json()
    # else:
    #     # If the response is not JSON (direct HTML), pass the context to the template
    #     race_data = response.context_data.get('race_data', [])
    
    # return render(request, 'raceDashboard.html', {'race_data': race_data})
    user_groups = request.session.get('user_groups', [])
    return render(request, 'raceDashboard.html', {'user_groups': user_groups})