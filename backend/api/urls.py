# api/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from food.views import (FavoriteViewSet, IngredientViewSet, RecipeViewSet,
                        ShoppingCartViewSet, TagViewSet)
from users.views import CustomUserViewSet

api_v1 = DefaultRouter()

api_v1.register(r'ingredients',
                IngredientViewSet, basename='ingredients')
api_v1.register(r'recipes', RecipeViewSet, basename='recipes')
api_v1.register(r'tags', TagViewSet, basename='tags')
api_v1.register(r'users', CustomUserViewSet, basename='users')
api_v1.register('favorites', FavoriteViewSet, basename='favorites')
api_v1.register('shopping_cart', ShoppingCartViewSet, basename='shopping-cart')


urlpatterns = [
    path('users/subscriptions/',
         CustomUserViewSet.as_view({'get': 'subscriptions'}),
         name='user-subscriptions'),
    # path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(api_v1.urls)),
]
