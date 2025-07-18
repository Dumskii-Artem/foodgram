# users/views.py
import os

from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404

from food.serializers import FollowSerializer
from users.models import Follow
from users.pagination import CustomPagination
from users.serializers import CustomUserSerializer
from rest_framework.response import Response
from rest_framework.permissions import (
     IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny)
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
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        print("set_avatar: Request data:", request.data)
        user = request.user

        if request.method == 'PUT':
            avatar = request.data.get('avatar')
            if not avatar:
                return Response(
                    {'avatar': ['Это поле обязательно.']},
                    status=status.HTTP_400_BAD_REQUEST)

            # Сохраняем текущий путь старого аватара (если есть)
            old_avatar_path = user.avatar.path if user.avatar else None

            try:
                user.avatar = CustomUserSerializer(
                    context={'request': request}
                ).fields['avatar'].to_internal_value(avatar)
            except Exception as e:
                return Response(
                    {'avatar': ['Некорректный формат изображения.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Создаем новый файл аватара, не удаляя пока старый
            # user.avatar = (
            #     CustomUserSerializer().fields['avatar'].to_internal_value(avatar))
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

        elif  request.method == 'DELETE':
            if (
                    user.avatar and
                    user.avatar.path and
                    os.path.isfile(user.avatar.path)
            ):
                try:
                    os.remove(user.avatar.path)
                except Exception:
                    pass  # подавляем ошибки удаления

            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        print("KWARGS:", kwargs)
        pk = kwargs.get('id')
        user = request.user
        target = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if user == target:
                return Response({'error': 'Нельзя подписаться на себя'}, status=400)
            if Follow.objects.filter(follower=user, following=target).exists():
                return Response({'error': 'Уже подписан'}, status=400)
            Follow.objects.create(follower=user, following=target)
            serializer = FollowSerializer(
                target, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            follow = Follow.objects.filter(follower=user, following=target)
            if follow.exists():
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Подписка не найдена'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def subscriptions(self, request):
        user = request.user
        # print(f'Запрос подписок от пользователя: {user} {request}')
        follows = Follow.objects.filter(follower=user)
        authors = User.objects.filter(pk__in=follows.values_list('following__id', flat=True))

        paginator = CustomPagination()
        paginated_authors = paginator.paginate_queryset(authors, request)

        serializer = FollowSerializer(
            paginated_authors,
            many=True,
            context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

