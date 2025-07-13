# users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet

router = DefaultRouter()
router.register('', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]
