from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCartItem, Tag, User)

admin.site.unregister(Group)


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
    related_name = 'follower_followes'


class HasSubscribersFilter(HasRelatedObjectsFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_subscribers'
    related_name = 'author_followes'


class HasFavoritesFilter(HasRelatedObjectsFilter):
    title = 'Есть избранное'
    parameter_name = 'has_favorites'
    related_name = 'favorites'


class HasRecipesFilter(HasRelatedObjectsFilter):
    title = 'Eсть в рецептах'
    parameter_name = 'has_recipes'
    related_name = 'recipes'


class RecipesCountMixin:
    list_display = ('recipes_count',)

    @admin.display(description='В рецептах')
    def recipes_count(self, user):
        return user.recipes.count()


@admin.register(User)
class UserProfileAdmin(UserAdmin, RecipesCountMixin,):
    model = User

    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_preview',
        'following_count',
        'followers_count',
        'is_staff',
        *RecipesCountMixin.list_display,
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

    @admin.display(description='Подписок')
    def following_count(self, user):
        return user.follower_followes.count()

    @admin.display(description='Подписчиков')
    def followers_count(self, author):
        return author.author_followes.count()

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
            return mark_safe(
                f'<img src="{user.avatar.url}" width="40" height="40" '
                f'style="object-fit: cover; border-radius: 4px;" />'
            )
        return '-'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'author')
    search_fields = ('follower__username', 'aurhor__username')
    list_filter = ('follower', 'author')


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

    def _range_filter(self, bounds, recipes=None):
        return (
            recipes
            or self.recipes
            or Recipe.objects.all()
        ).filter(cooking_time__range=bounds)

    def lookups(self, request, model_admin):
        self.recipes = model_admin.get_queryset(request)
        times = list(self.recipes.values_list('cooking_time', flat=True))
        if len(set(times)) < 3:
            return []

        times.sort()
        short_time_max = times[len(times) // 3]
        medium_time_max = times[2 * len(times) // 3]

        self.thresholds = {
            'fast': {
                'range': (0, short_time_max - 1),
                'label': f'быстрее {short_time_max} мин',
            },
            'medium': {
                'range': (short_time_max, medium_time_max - 1),
                'label': f'быстрее {medium_time_max} мин',
            },
            'long': {
                'range': (medium_time_max, times[-1] + 1),
                'label': 'долго',
            },
        }

        return [
            (
                key,
                f"{value['label']} "
                f"({self._range_filter(value['range']).count()})"
            )
            for key, value in self.thresholds.items()
        ]

    def queryset(self, request, queryset):
        selected = self.value()
        if selected in self.thresholds:
            return self._range_filter(
                bounds=self.thresholds[selected]['range'],
                recipes=queryset
            )
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_time', 'author',
        'favorites_count', 'products_list', 'tags_list', 'image_tag'
    )
    search_fields = ('name', 'author__username')
    list_filter = ('author', CookingTimeFilter, 'tags')
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _favorites_count=Count(
                'favorites', distinct=True)
        )

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe._favorites_count

    @admin.display(description='Продукты')
    def products_list(self, recipe):
        return mark_safe('<br>'.join([
            f'{ri.ingredient.name} - '
            f'{ri.amount} {ri.ingredient.measurement_unit}'
            for ri in recipe.ingredients_in_recipe.all()])
        )

    @admin.display(description='Теги')
    def tags_list(self, recipe):
        return mark_safe('<br>'.join([tag.name for tag in recipe.tags.all()]))

    @admin.display(description='Изображение')
    def image_tag(self, recipe):
        return mark_safe(
            f'<img src="{recipe.image.url}" '
            f'style="height: 50px; object-fit: cover; border-radius: 4px;" />'
        )
        return ''
