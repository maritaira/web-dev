from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse
import subprocess
from races.models import Race, Car
from django.shortcuts import render, get_object_or_404


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def start_training(request):
    if request.method == "POST":
        try:
            # Run yamlGen.py
            yaml_process = subprocess.run(["python3", "ml_integration/yamlGen.py"], capture_output=True, text=True)
            if yaml_process.returncode != 0:
                return JsonResponse({"error": "yamlGen.py failed", "details": yaml_process.stderr}, status=500)

            # Run data_split.py after yamlGen.py succeeds
            split_process = subprocess.run(["python3", "ml_integration/data_split.py"], capture_output=True, text=True)
            if split_process.returncode != 0:
                return JsonResponse({"error": "data_split.py failed", "details": split_process.stderr}, status=500)

            return JsonResponse({"message": "Training process started successfully"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

