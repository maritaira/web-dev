from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImageViewSet, VideoViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'images', ImageViewSet, basename='image')
router.register(r'videos', VideoViewSet, basename='video')

urlpatterns = [
    path('', include(router.urls)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
