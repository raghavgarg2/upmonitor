from .views import RegisterAPIView,LoginAPIView
from django.urls import path

urlpatterns = [
    path("register/",RegisterAPIView.as_view()),
    path("login/",LoginAPIView.as_view())
]