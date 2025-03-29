from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImageViewSet, VideoViewSet
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


router = DefaultRouter()
router.register(r'images', ImageViewSet, basename='image')
router.register(r'videos', VideoViewSet, basename='video')

urlpatterns = [
    path('', include(router.urls)),
]

# Redirect function
def redirect_to_cars(request):
    return redirect('pages:all_cars')  # Redirect to My Cars page

urlpatterns = [
    path('api/', include(router.urls)),  # API endpoints for images/videos
    
    # Redirect users if they try to access media directly
    path('images/', redirect_to_cars),
    path('videos/', redirect_to_cars),
]

# Ensure media files are not served in production
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)