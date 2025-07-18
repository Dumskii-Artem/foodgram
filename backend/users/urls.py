# users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet

api_v1 = DefaultRouter()
api_v1.register('', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(api_v1.urls)),
]
