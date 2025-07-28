# api/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    UserWithSubscriptionViewSet
)

api = DefaultRouter()

api.register(r'ingredients',
                IngredientViewSet, basename='ingredients')
api.register(r'recipes', RecipeViewSet, basename='recipes')
api.register(r'tags', TagViewSet, basename='tags')
api.register(r'users', UserWithSubscriptionViewSet, basename='users')
# api.register('favorites', FavoriteViewSet, basename='favorites')
# api.register('shopping_cart', ShoppingCartViewSet, basename='shopping-cart')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(api.urls)),
]
