# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import CustomUserViewSet

api_v1 = DefaultRouter()

api_v1.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(api_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]
    # path('users/', include('users.urls')),             # твой кастомный ViewSet
    # path('', include('djoser.urls.base')),             # регистрация и т.п.


# urlpatterns = [
#
#     path('', include('djoser.urls')),
#     # регистрация, вход, выход, смена пароля и т.п.
#     path('auth/', include('djoser.urls.authtoken')),  # токен-аутентификация
#     path('users/', include('users.urls')),  # твои кастомные роуты, если нужны
#
#
#     # path('', include('djoser.urls.base')),  # без пользователей
#     # path('', include('djoser.urls')),
#     # path('auth/', include('djoser.urls.authtoken')),
# ]
#
#     path('users/me/avatar/', UserView.as_view(), name='avatar'),
# ]

