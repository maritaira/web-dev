from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .models import Image
from .serializers import ImageSerializer
# from django.conf import settings

# Create your views here.
class ImageViewSet(ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    
    def list(self, request):
        # print("GET request received")
        username = request.query_params.get("username")
        car_name = request.query_params.get("car_name")
        
        if not username or not car_name:
            return Response({"error": "username and car_name are required."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Image.objects.filter(username=username, car_name=car_name)
        # print("filtered images in list()")
        # print(f"Queryset count: {queryset.count()}")  # Debugging
        # for obj in queryset:
        #     print(obj)  # Ensure queryset actually contains objects

        serializer = self.get_serializer(queryset, many=True)
        # print("serializer initialized")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        car_name = request.data.get('car_name')
        images = request.FILES.getlist('images')
        
        
        if not images:
            return Response({'error': 'No files provided.'}, status=status.HTTP_400_BAD_REQUEST)
        if not username or not car_name:
            return Response({'error': 'username and car_name are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        uploads = []
        
        try:
            for image in images:
                serializer = self.get_serializer(data={'username': username, 
                                                       'car_name': car_name, 
                                                       'image': image
                                                       })
                
                serializer.is_valid(raise_exception=True)
                # print("passed isvalid serializer")
                self.perform_create(serializer)
                # print(f"Serializer.data: {serializer.data}")
                uploads.append(serializer.data)
                print(f"Successfully added {image.name}")
                
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return Response(
                {"detail": {str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(uploads, status=status.HTTP_201_CREATED)
