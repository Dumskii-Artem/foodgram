from django.urls import path

from food.views import short_link_redirect_view

urlpatterns = [
    path('s/<int:pk>/', short_link_redirect_view, name='recipe-short-link'),
]
