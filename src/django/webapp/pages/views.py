from django.shortcuts import render, redirect
from .forms import ImageUploadForm
# Create your views here.
from django.http import HttpResponse
import requests
from media.models import Video, Image

import boto3

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
    return render(request, 'dashboard.html', {'image': image})


def all_videos(request):
    videos = Video.objects.all()
    context = {
        'videos': videos
    }

    return render(request, 'all_videos.html', context)


def view_video(request):
    return

def login_pg(request):
    return render(request, 'login.html')

def create_acc(request):
    return render(request, 'create_acc.html')
def all_cars(request):
    return render(request, 'all_cars.html')


def upcoming_races(request):
    return render (request, 'upcoming_races.html')

MEDIA_API_URL = "http://127.0.0.1:8000/media/"

def play_video(request):
    print("in play_video")
    video = None
    error_message = None
    race = request.GET.get("race", "")
    print(race)
    
    if race:
        fetch_video_url = f"{MEDIA_API_URL}videos/?race={race}"
        try:
            response = requests.get(fetch_video_url)
            
            if response.status_code == 200:
                video_data = response.json()
                print(video_data)
                
                video_url = video_data[0]["video_url"]  # Assuming the video URL is returned as "video_url"
                
                # Check if the video already exists in the database
                video_exists = Video.objects.filter(file=video_url).exists()
                
                if not video_exists:
                    Video.objects.create(race=race, file=video_url)
                    print("New video created.")
                else:
                    print("Video already exists in the database.")
                
                video = video_data
                
            else:
                print("Error, could not retrieve video")
                return render(request, "play_video.html", {"error": "Could not retrieve video."})
        except requests.exceptions.RequestException as e:
            print(str(e))
            error_message = "Video not found"
            return render(request, "play_video.html", {"error": f"Error retrieving video: {str(e)}"})

    return render(request, "play_video.html", {"video": video, "error_message": error_message})



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
