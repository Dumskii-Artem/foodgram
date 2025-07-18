# food/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import User, Follow


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    # list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    # search_fields = ('email', 'username')
    # ordering = ('email',)

    list_display = ('id', 'username', 'email', 'first_name',
                    'last_name', 'avatar_preview', 'avatar_link', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('first_name', 'last_name', 'email', 'avatar')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('id',)

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                ('<img src="{}" width="40" height="40"'
                ' style="object-fit: cover; border-radius: 4px;" />'),
                obj.avatar.url
            )
        return "-"

    avatar_preview.short_description = "Аватар"

    def avatar_link(self, obj):
        if obj.avatar:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.avatar.url,
                obj.avatar.name.split('/')[-1]
            )
        return "-"

    avatar_link.short_description = "Файл аватара"

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following')
    search_fields = ('follower__username', 'following__username')
    list_filter = ('follower', 'following')
