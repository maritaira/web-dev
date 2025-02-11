from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
import requests


def index(request):
    return HttpResponse("Hello, world. You're at the pages view.")


def dashboard(request):
    return render(request, 'dashboard.html')

def all_videos(request):
    return render(request, 'all_videos.html')

def login_pg(request):
    return render(request, 'login.html')

def create_acc(request):
    return render(request, 'create_acc.html')
def all_cars(request):
    return render(request, 'all_cars.html')
def upcoming_races(request):
    return render (request, 'upcoming_races.html')

MEDIA_API_URL = "http://127.0.0.1:8000/media/images/"

def display_images(request):
    """Fetch images for car"""
    # print("in display_images()")
    images = []
    username = request.GET.get("username", "")
    car_name = request.GET.get("car_name", "")
    # print(username)
    # print(car_name)
    
    if username and car_name:
        fetch_api_url = f"{MEDIA_API_URL}?username={username}&car_name={car_name}"
        # print(fetch_api_url)
        try:
            response = requests.get(fetch_api_url)
            # print("get request sent")
            # print(response.status_code)
            if response.status_code == 200:
                images = response.json()  # List of image URLs
                # print("successfully fetched images")
            else:
                return render(request, "image_upload.html", {"error": "Could not retrieve images."})
        except requests.exceptions.RequestException as e:
            return render(request, "image_upload.html", {"error": f"Error retrieving images: {str(e)}"})

    return render(request, "image_upload.html", {"images": images, "username": username, "car_name": car_name})


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