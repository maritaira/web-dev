from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImageViewSet, VideoViewSet

router = DefaultRouter()
router.register(r'images', ImageViewSet, basename='image')
router.register(r'videos', VideoViewSet, basename='video')

urlpatterns = [
    path('', include(router.urls)),
]
    