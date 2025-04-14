from django.shortcuts import render
import json
# Create your views here.
from django.http import HttpResponse, JsonResponse
import subprocess
from races.models import Race, Car, RaceParticipant
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .data_split import split_dataset_s3
from django.conf import settings
from . import transfer_learning_copy
from . import yamlGen
import shutil
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


def get_user_class_pairs(race_id):
    participants = RaceParticipant.objects.filter(race=race_id)
    
    print("received participants")
    
    pairs = []
    
    for participant in participants:
        pairs.append((participant.car_owner.username, participant.car.name))
    
    print(pairs)
        
    return pairs



@csrf_exempt
def start_training(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            race_id = data.get("race_id")
            race_name = data.get("race_name")
            owner = request.user.username
            num_cars = data.get("num_cars")
            car_names = data.get("car_names")

            print("🔥 Training Request Received in ml_integration/views.py")
            print("Race ID:", race_id)
            print("Race Name: ", race_name)
            print("OWNER :", owner)
            print("Number of Cars:", num_cars)
            print("Car Names:", car_names)

            if not race_id or num_cars is None or not car_names:
                return JsonResponse({"error": "Missing required data"}, status=400)

            # Run yamlGen.py
            # yaml_process = subprocess.run(
            #     ["python3", "./ml_integration/yamlGen.py"],  # Ensure correct path
            #     input=json.dumps({"race_id": race_id, "num_classes": num_cars, "classes": car_names}),
            #     capture_output=True,
            #     text=True
            # )
            yamlGen.generateYam(
                race_id=race_id,
                owner=owner,
                race_name=race_name,
                num_cars=num_cars,
                classes=car_names
            )

            print("yamlGen successful!")

            # Data Split
            
            src_bucket = settings.AWS_STORAGE_CARS_BUCKET_NAME
            dst_bucket = settings.AWS_STORAGE_RACES_BUCKET_NAME
            source_prefix = ""
            dst_prefix = f"{owner}/{race_name}/dataset/"
            allowed_user_class_pairs = get_user_class_pairs(race_id)
            
            split_dataset_s3(src_bucket, dst_bucket, source_prefix, dst_prefix, allowed_user_class_pairs=allowed_user_class_pairs)
            
            #Run transfer_learning copy
            
            transfer_learning_copy.main(owner, race_name, race_id, allowed_user_class_pairs)
            # # Run data_split.py
            # split_process = subprocess.run(
            #     ["python3", "./ml_integration/data_split.py"],  # Ensure correct path
            #     capture_output=True,
            #     text=True
            # )

            # print("📂 data_split.py Output:", split_process.stdout)
            # print("⚠️ data_split.py Error (if any):", split_process.stderr)

            # if split_process.returncode != 0:
            #     return JsonResponse({"error": "data_split.py failed", "details": split_process.stderr}, status=500)

            return JsonResponse({"message": "Training process started successfully"})

        except Exception as e:
            print("🔥 Django Error:", str(e))
            return JsonResponse({"error": str(e)}, status=500)