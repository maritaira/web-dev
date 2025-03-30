from django.urls import path
from . import views

urlpatterns = [
    path("sign-up/", views.SignUpView.as_view(), name="sign_up"),
    path("sign-in/", views.SignInView.as_view(), name="sign_in"),
    path("sign-out/", views.SignOutView.as_view(), name="sign_out"),
]