"""
URL configuration for webapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from . import views
from pages.views import login_pg
from django.contrib import admin

handler404 = "webapp.views.custom_404_view"  # Register the 404 handler

urlpatterns = [
    path('', login_pg, name='login'),
    # path('', views.index, name='index'),  # Route for the app's homepage
    path('pages/', include('pages.urls')),
    ##path('admin/', admin.site.urls),
    path('media/', include('media.urls')),
    path('accounts/', include('accounts.urls')),
    path('auth/', include('accounts.urls')),
    path('', include('races.urls'))
]



##controls paths to apps


