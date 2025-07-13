# user/serializers.py

import base64
import os
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer

from rest_framework import serializers

User = get_user_model()

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):

            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=filename)
        return super().to_internal_value(data)

class CustomUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_subscribed',
                  'first_name', 'last_name', 'avatar')
        read_only_fields = ('id',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.follower.filter(following=obj).exists()


#
#     def to_representation(self, value):
#         if not value:
#             return None
#         request = self.context.get('request', None)
#         if request is not None:
#             return request.build_absolute_uri(value.url)
#         return value.url
#
#
# class UserSerializer(serializers.ModelSerializer):
#     avatar = Base64ImageField(required=False, allow_null=True)
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'email',
#                   'first_name', 'last_name', 'avatar')
#         read_only_fields = ('id',)
#
#     def update(self, instance, validated_data):
#         # удаляем старый файл с аватаром
#         new_avatar = validated_data.get('avatar', None)
#         if new_avatar and instance.avatar:
#             old_avatar_path = instance.avatar.path
#             if os.path.exists(old_avatar_path):
#                 try:
#                     os.remove(old_avatar_path)
#                 except Exception as e:
#                     # логирование, если нужно
#                     pass
#
#         instance.avatar = new_avatar or instance.avatar
#         instance.save()
#         return instance

# class UserListSerializer(serializers.ModelSerializer):
#     is_subscribed = serializers.SerializerMethodField()
#     avatar = serializers.ImageField(allow_null=True)
#
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'first_name', 'last_name',
#                   'email', 'is_subscribed', 'avatar')
#
#     def get_is_subscribed(self, obj):
#         request = self.context.get('request')
#         if request and not request.user.is_anonymous:
#             return False  # или логика подписок
#         return False



