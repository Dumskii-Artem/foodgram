# backend/users/models.py

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from . import constants as uconst

username_validator = RegexValidator(
    regex=r'^[\w.@-]+$',
    message=('Имя пользователя может содержать'
             ' только буквы, цифры и символы @ . - _')
)


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=uconst.USER_EMAIL_LENGTH,
        verbose_name="Email"
    )
    first_name = models.CharField(
        max_length=uconst.USER_FIRST_NAME_LENGTH,
        verbose_name="First name"
    )
    last_name = models.CharField(
        max_length=uconst.USER_LAST_NAME_LENGTH,
        verbose_name="Last name"
    )
    username = models.CharField(
        max_length=uconst.USER_USERNAME_LENGTH,
        unique=True,
        verbose_name="Username",
        validators=[username_validator],
    )
    avatar = models.ImageField(
        upload_to='avatars/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email


class Follow(models.Model):
    following = models.ForeignKey(
        User,
        related_name='following',  # на кого подписаны
        on_delete=models.CASCADE
    )
    follower = models.ForeignKey(
        User,
        related_name='follower',  # подписчик пользователя
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('following', 'follower')

    def __str__(self):
        return f'{self.follower} подписан на {self.following}'
