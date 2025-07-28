# backend/food/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCartItem, Tag, User)


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'

    def lookups(self, request, model_admin):
        return [('yes', 'Да'), ('no', 'Нет')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(follower__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(follower__isnull=True)
        return queryset


class HasSubscribersFilter(admin.SimpleListFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_subscribers'

    def lookups(self, request, model_admin):
        return [('yes', 'Да'), ('no', 'Нет')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(following__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(following__isnull=True)
        return queryset


class HasRecipesFilter(admin.SimpleListFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return [('yes', 'Да'), ('no', 'Нет')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipes__isnull=True)
        return queryset


class HasFavoritesFilter(admin.SimpleListFilter):
    title = 'Есть избранное'
    parameter_name = 'has_favorites'

    def lookups(self, request, model_admin):
        return [('yes', 'Да'), ('no', 'Нет')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(favorites__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(favorites__isnull=True)
        return queryset



@admin.register(User)
class UserProfileAdmin(UserAdmin):
    model = User

    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_preview',
        'recipe_count',
        'following_count',
        'followers_count',
        'is_staff',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        HasRecipesFilter,
        HasFavoritesFilter,
        HasSubscriptionsFilter,  # кого читает пользователь
        HasSubscribersFilter,  # кто читает пользователя
    )

    @staticmethod
    def full_name(user):
        return f'{user.first_name} {user.last_name}'

    # @mark_safe
    # def avatar_preview(self, user):
    #     if user.avatar:
    #         return (
    #             f'<img src="{user.avatar.url}" width="40" height="40" '
    #             f'style="object-fit: cover; border-radius: 4px;" />'
    #         )
    #     return '-'
    # avatar_preview.short_description = 'Аватар'

    @staticmethod
    def recipe_count(user):
        return user.recipes.count()
    recipe_count.short_description = 'Рецептов'

    @staticmethod
    def following_count(user):
        return user.following.count()

    following_count.short_description = 'Подписок'


    @staticmethod
    def followers_count(user):
        return user.followers.count()

    followers_count.short_description = 'Подписчиков'


    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': (
            'first_name', 'last_name', 'email', 'avatar')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions'),
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




    @admin.display(description='Аватар')
    def avatar_preview(self, user):
        if user.avatar:
            return format_html(
                '<img src=\'{}\' width=\'40\' height=\'40\' '
                'style=\'object-fit: cover; border-radius: 4px;\' />',
                user.avatar.url
            )
        return '-'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'author')
    search_fields = ('follower__username', 'aurhor__username')
    list_filter = ('follower', 'author')


class RecipesCountMixin:
    def recipes_count(self, obj):
        return obj.recipes.count()
    recipes_count.short_description = 'В рецептах'


@admin.register(Tag)
class TagAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'recipes_count')
    search_fields = ('name', 'slug')


class HasRecipesFilter(admin.SimpleListFilter):
    title = 'есть в рецептах'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return [('yes', 'Есть'), ('no', 'Нет')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        elif self.value() == 'no':
            return queryset.filter(recipes__isnull=True)
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', HasRecipesFilter)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('recipes')


@admin.register(Favorite, ShoppingCartItem)
class UserRecipeRelationAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_time', 'author',
        'favorites_count', 'products_list', 'tags_list', 'image_tag'
    )
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'author', 'cooking_time',)
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _favorites_count=Count('favorites', distinct=True))

    def favorites_count(self, obj):
        return obj._favorites_count

    favorites_count.short_description = 'В избранном'

    def products_list(self, obj):
        ingredients = obj.ingredients.all()
        names = [ingredient.name for ingredient in ingredients]
        return ', '.join(names)
    products_list.short_description = 'Продукты'

    def tags_list(self, obj):
        tags = obj.tags.all()
        names = [tag.name for tag in tags]
        return ', '.join(names)
    tags_list.short_description = 'Теги'

    @mark_safe
    def image_tag(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="height: 50px;"/>'
        return '(Нет изображения)'
    image_tag.short_description = 'Изображение'


    # Фильтр по времени готовки с тремя интервалами и подсчётом количества
    class CookingTimeFilter(admin.SimpleListFilter):
        title = 'Время готовки'
        parameter_name = 'cooking_time_bin'

        def lookups(self, request, model_admin):
            # Определяем пороги N и M
            qs = model_admin.get_queryset(request)
            times = list(qs.values_list('cooking_time', flat=True))
            if not times:
                return []
            times.sort()
            n = times[len(times) // 3]
            m = times[2 * len(times) // 3]

            count_fast = qs.filter(cooking_time__lt=n).count()
            count_medium = qs.filter(cooking_time__gte=n, cooking_time__lt=m).count()
            count_long = qs.filter(cooking_time__gte=m).count()

            return [
                (f'fast', f'быстрее {n} мин ({count_fast})'),
                (f'medium', f'быстрее {m} мин ({count_medium})'),
                (f'long', f'долго ({count_long})'),
            ]

        def queryset(self, request, queryset):
            value = self.value()
            if value == 'fast':
                return queryset.filter(cooking_time__lt=self.get_n(request))
            elif value == 'medium':
                return queryset.filter(
                    cooking_time__gte=self.get_n(request),
                    cooking_time__lt=self.get_m(request)
                )
            elif value == 'long':
                return queryset.filter(cooking_time__gte=self.get_m(request))
            return queryset

        def get_n(self, request):
            qs = self.model_admin.get_queryset(request)
            times = list(qs.values_list('cooking_time', flat=True))
            times.sort()
            return times[len(times) // 3] if times else 0

        def get_m(self, request):
            qs = self.model_admin.get_queryset(request)
            times = list(qs.values_list('cooking_time', flat=True))
            times.sort()
            return times[2 * len(times) // 3] if times else 0

        def __init__(self, request, params, model, model_admin):
            super().__init__(request, params, model, model_admin)
            self.model_admin = model_admin

    list_filter = ('author', CookingTimeFilter)
