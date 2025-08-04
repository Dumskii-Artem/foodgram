from collections import Counter

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from food.constants import INGREDIENT_MIN_AMOUNT, RECIPE_MIN_COOKING_TIME
from food.models import (Favorite, Follow, Ingredient, Recipe,
                         RecipeIngredient, ShoppingCartItem, Tag)
from library.base64ImageField import Base64ImageField

User = get_user_model()


class FoodgramUserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (*DjoserUserSerializer.Meta.fields, 'avatar', 'is_subscribed')
        read_only_fields = fields

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (
            request
            and not request.user.is_anonymous
            and Follow.objects.filter(author=author,
                                      follower=request.user).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(
        min_value=INGREDIENT_MIN_AMOUNT,
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientReadSerializer(
        source='ingredients_in_recipe',
        many=True
    )
    author = FoodgramUserSerializer()
    tags = TagSerializer(many=True)

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time')
        read_only_fields = fields

    def check_user_status(self, recipe, model_class):
        request = self.context.get('request')
        return (
            request
            and not request.user.is_anonymous
            and model_class.objects.filter(user=request.user,
                                           recipe=recipe).exists()
        )

    def get_is_favorited(self, recipe):
        return self.check_user_status(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self.check_user_status(recipe, ShoppingCartItem)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(
        many=True,
        required=True,
        label='Ингредиенты',
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        label='Теги',
    )
    cooking_time = serializers.IntegerField(
        min_value=RECIPE_MIN_COOKING_TIME,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data

    def create_ingredients(self, ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['ingredient'].id,
                amount=item['amount']
            )
            for item in ingredients
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        validated_data['author'] = self.context['request'].user
        recipe = super().create(validated_data)

        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        tags_data = validated_data.pop('tags', [])

        instance.tags.set(tags_data)
        instance.ingredients_in_recipe.all().delete()
        self.create_ingredients(ingredients_data, instance)
        return super().update(instance, validated_data)

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент.')
        duplicate_ids = {
            id_ for id_, count in
            Counter(item['ingredient'].id for item in ingredients).items()
            if count > 1
        }
        if not duplicate_ids:
            return ingredients

        names = Ingredient.objects.filter(
            id__in=duplicate_ids).values_list('name', flat=True)

        raise serializers.ValidationError(
            f'Ингредиенты не должны повторяться: {names}.')

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один тег.')

        duplicate_ids = {
            id_ for id_, count in
            Counter(getattr(tag, 'id') for tag in tags).items()
            if count > 1
        }
        if not duplicate_ids:
            return tags

        names = (Tag.objects.filter(id__in=duplicate_ids)
                 .values_list('name', flat=True))
        raise serializers.ValidationError(
            f'Теги не должны повторяться: {names}.'
        )

    def validate(self, data):
        request_method = self.context['request'].method

        if request_method in ('POST', 'PATCH'):
            if 'ingredients' not in data:
                raise serializers.ValidationError(
                    {'ingredients': 'Это поле обязательно.'})
            if 'tags' not in data:
                raise serializers.ValidationError(
                    {'tags': 'Это поле обязательно.'})

        return data


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, followed_user):
        user = self.context['request'].user
        return user.is_authenticated and Follow.objects.filter(
            follower=user, author=followed_user
        ).exists()

    class Meta:
        model = User
        fields = (*DjoserUserSerializer.Meta.fields,
                  'avatar', 'is_subscribed')
        read_only_fields = fields


class FollowedUserSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta:
        model = User
        fields = (*UserSerializer.Meta.fields,
                  'recipes', 'recipes_count')
        read_only_fields = fields

    def get_recipes(self, obj):
        return ShortRecipeSerializer(
            obj.recipes.all()[
                :int(self.context['request'].
                     GET.get('recipes_limit', 10 ** 10))
            ],
            many=True,
            context=self.context
        ).data
