# backend/food/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCartItem, Tag, User)


class HasRelatedObjectsFilter(admin.SimpleListFilter):
    LOOKUP_CHOICES = [('yes', 'Да'), ('no', 'Нет')]

    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return (queryset.
                    filter(**{f'{self.related_name}__isnull': False})
                    .distinct()
                    )
        if self.value() == 'no':
            return queryset.filter(**{f'{self.related_name}__isnull': True})
        return queryset


class HasSubscriptionsFilter(HasRelatedObjectsFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'
    related_name = 'follower'


class HasSubscribersFilter(HasRelatedObjectsFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_subscribers'
    related_name = 'following'


class HasFavoritesFilter(HasRelatedObjectsFilter):
    title = 'Есть избранное'
    parameter_name = 'has_favorites'
    related_name = 'favorites'


class HasRecipesFilter(HasRelatedObjectsFilter):
    title = 'Eсть в рецептах'
    parameter_name = 'has_recipes'
    related_name = 'recipes'


class UserRecipesCountMixin:
    @admin.display(description='Рецептов')
    def recipe_count(self, obj):
        return obj.recipes.count()


class SubscriptionsCountMixin:
    @admin.display(description='Подписок')
    def following_count(self, user):
        return user.follower_followes.count()

    @admin.display(description='Подписчиков')
    def followers_count(self, author):
        return author.author_followes.count()


@admin.register(User)
class UserProfileAdmin(UserAdmin,
                       UserRecipesCountMixin,
                       SubscriptionsCountMixin):
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

    @admin.display(description='Полное имя')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

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
    list_display = ('recipes_count',)

    def recipes_count(self, obj):
        return obj.recipes.count()
    recipes_count.short_description = 'В рецептах'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin, RecipesCountMixin):
    list_display = ('id', 'name', 'slug', *RecipesCountMixin.list_display)
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',
                    *RecipesCountMixin.list_display)
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


# Фильтр по времени готовки с тремя интервалами и подсчётом количества
class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time_bin'

    def _range_filter(self, qs, bounds):
        return qs.filter(cooking_time__range=bounds)

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        times = list(qs.values_list('cooking_time', flat=True))
        if len(set(times)) < 3:
            return []

        times.sort()
        self.n = times[len(times) // 3]
        self.m = times[2 * len(times) // 3]
        self.max_time = times[-1] + 1

        return [
            ('fast',
             f'быстрее {self.n} мин '
             f'({self._range_filter(qs, (0, self.n)).count()})'
             ),
            ('medium',
             f'быстрее {self.m} мин '
             f'({self._range_filter(qs, (self.n, self.m)).count()})'
             ),
            ('long',
             f'долго '
             f'({self._range_filter(qs, (self.m, self.max_time)).count()})'
             ),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if not value or not hasattr(self, 'n') or not hasattr(self, 'm'):
            return queryset

        if value == 'fast':
            return self._range_filter(queryset, (0, self.n))
        elif value == 'medium':
            return self._range_filter(queryset, (self.n, self.m))
        elif value == 'long':
            return self._range_filter(queryset, (self.m, self.max_time))

        return queryset


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
            _favorites_count=Count('favorite', distinct=True)
        )
        # return qs.annotate(
        #     _favorites_count=Count('favorite_set', distinct=True))

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe._favorites_count

    @admin.display(description='Продукты')
    def products_list(self, recipe):
        return '<br>'.join([
            f'{ri.ingredient.name} - '
            f'{ri.amount} {ri.ingredient.measurement_unit}'
            for ri in recipe.ingredients_in_recipe.all()])

    @admin.display(description='Теги')
    def tags_list(self, recipe):
        return '<br>'.join([tag.name for tag in recipe.tags.all()])

    @mark_safe
    def image_tag(self, recipe):
        if recipe.image:
            return f'<img src="{recipe.image.url}" style="height: 50px;"/>'
        return ''
    image_tag.short_description = 'Изображение'

    list_filter = ('author', CookingTimeFilter)
