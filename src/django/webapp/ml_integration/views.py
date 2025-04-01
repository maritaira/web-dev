from django.shortcuts import render
import json
# Create your views here.
from django.http import HttpResponse, JsonResponse
import subprocess
from races.models import Race, Car
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt



def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

# def generate_yaml(race_id):
#     """Generates a YAML file with race and car details"""
#     race = Race.objects.filter(id=race_id)
#     cars = Car.objects.filter(race=race).select_related("owner")

#     # Prepare data
#     data = {
#         "race_name": race.name,
#         "num_classes": cars.count(),
#         "classes": [{"id": i + 1, "label": car.name} for i, car in enumerate(cars)]
#     }

#     # Create config directory if not exists
#     config_dir = f"race-{race.id}/config"
#     os.makedirs(config_dir, exist_ok=True)

#     # Save YAML file
#     yaml_filename = f"{config_dir}/config_{uuid.uuid4().hex[:8]}.yaml"
#     with open(yaml_filename, "w") as file:
#         yaml.dump(data, file, default_flow_style=False)

#     return yaml_filename

@csrf_exempt
def start_training(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            race_id = data.get("race_id")
            num_cars = data.get("num_cars")
            car_names = data.get("car_names")

            print("🔥 Training Request Received in ml_integration/views.py")
            print("Race ID:", race_id)
            print("Number of Cars:", num_cars)
            print("Car Names:", car_names)

            if not race_id or num_cars is None or not car_names:
                return JsonResponse({"error": "Missing required data"}, status=400)

            # Run yamlGen.py
            yaml_process = subprocess.run(
                ["python3", "./ml_integration/yamlGen.py"],  # Ensure correct path
                input=json.dumps({"race_id": race_id, "num_classes": num_cars, "classes": car_names}),
                capture_output=True,
                text=True
            )

            print("📄 yamlGen.py Output:", yaml_process.stdout)
            print("⚠️ yamlGen.py Error (if any):", yaml_process.stderr)

            if yaml_process.returncode != 0:
                return JsonResponse({"error": "yamlGen.py failed", "details": yaml_process.stderr}, status=500)

            # Run data_split.py
            split_process = subprocess.run(
                ["python3", "./ml_integration/data_split.py"],  # Ensure correct path
                capture_output=True,
                text=True
            )

            print("📂 data_split.py Output:", split_process.stdout)
            print("⚠️ data_split.py Error (if any):", split_process.stderr)

            if split_process.returncode != 0:
                return JsonResponse({"error": "data_split.py failed", "details": split_process.stderr}, status=500)

            return JsonResponse({"message": "Training process started successfully"})

        except Exception as e:
            print("🔥 Django Error:", str(e))
            return JsonResponse({"error": str(e)}, status=500)