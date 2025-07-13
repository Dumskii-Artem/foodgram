# users/views.py
import os

from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework.decorators import action

from users.serializers import CustomUserSerializer
from rest_framework.response import Response
from rest_framework.permissions import (
     IsAuthenticatedOrReadOnly, IsAuthenticated)
from rest_framework import status

User = get_user_model()

class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated]
            )
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def set_avatar(self, request):
        user = request.user
        avatar = request.data.get('avatar')

        if not avatar:
            return Response(
                {'avatar': ['Это поле обязательно.']}, status=400)

        # Сохраняем текущий путь старого аватара (если есть)
        old_avatar_path = user.avatar.path if user.avatar else None

        # Создаем новый файл аватара, не удаляя пока старый
        user.avatar = (
            CustomUserSerializer().fields['avatar'].to_internal_value(avatar))
        user.save()

        # Удаляем старый файл, если он был и отличается от нового
        if old_avatar_path and os.path.isfile(old_avatar_path):
            try:
                # Проверяем, что новый файл не совпадает с удаляемым
                if old_avatar_path != user.avatar.path:
                    os.remove(old_avatar_path)
            except Exception:
                # На всякий случай подавляем ошибку удаления,
                # чтобы не ломать ответ
                pass

        return Response(
            {'avatar': user.avatar.url if user.avatar else None},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def delete_avatar(self, request):
        user = request.user

        # Если аватар есть, удаляем файл
        if user.avatar and user.avatar.path and os.path.isfile(user.avatar.path):
            try:
                os.remove(user.avatar.path)
            except Exception:
                pass  # подавляем ошибки удаления

        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
