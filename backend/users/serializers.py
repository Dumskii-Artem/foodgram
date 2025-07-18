# user/serializers.py

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer

from rest_framework import serializers

from library.base64ImageField import Base64ImageField

User = get_user_model()


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

    def get_avatar(self, obj):
        # Или obj.avatar.url, если поле ImageField
        return None  # Если нет аватаров, верни None
