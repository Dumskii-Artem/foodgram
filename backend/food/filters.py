# backend/food/filters.py

from django_filters import rest_framework as filters

from food.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        label='tags',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and not user.is_anonymous:

            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(shopping_carts__user=user)
        return queryset
