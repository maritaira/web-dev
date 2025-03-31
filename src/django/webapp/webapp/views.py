# projectApp/views.py
from django.http import HttpResponse
from django.shortcuts import render
import logging

def index(request):
    return HttpResponse("Hello, World!")  # Test view

def custom_404_view(request, exception):
    try:
        user_groups = request.session.get('user_groups', [])  # Fetch user groups from session
        return render(request, "404.html", {"user_groups": user_groups}, status=404)
    except Exception as e:
        # Log the exception for debugging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in custom 404 handler: {e}")
        return render(request, "404.html", {"error": "An error occurred while processing the request."}, status=404)
