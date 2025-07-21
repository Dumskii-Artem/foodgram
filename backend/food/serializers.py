# backend/food/serializers.py
import uuid

from rest_framework import serializers

from library.base64ImageField import Base64ImageField
from users.models import Follow, User
from users.serializers import CustomUserSerializer

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, RecipeTag,
                     ShoppingCartItem, Tag)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    # image = Base64ImageField(required=False, allow_null=True)

    ingredients = RecipeIngredientReadSerializer(
        source='ingredient_list',
        many=True
    )

    author = CustomUserSerializer()
    tags = TagSerializer(many=True)

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time')

    def check_user_status(self, obj, model_class):
        user = self.context.get('request')
        return bool(
            user
            and user.user.is_authenticated
            and model_class.objects.filter(
                user=user.user, recipe=obj
            ).exists()
        )

    def get_is_favorited(self, obj):
        return self.check_user_status(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.check_user_status(obj, ShoppingCartItem)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(
        many=True,
        label='Ингредиенты',
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        label='Теги',
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
        serializer = RecipeReadSerializer(
            instance,
            context={'request': self.context['request']}
        )
        return serializer.data

    def create_tags(self, tags, recipe):
        recipe.tags.set(tags)

    def create_ingredients(self, ingredients, recipe):
        for ingredient_data in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient_data['id']),
                amount=ingredient_data['amount']
            )

    def generate_short_link(self):
        for _ in range(10):  # 10 попыток
            short_id = uuid.uuid4().hex[:6]
            if not Recipe.objects.filter(short_link=short_id).exists():
                return short_id
        raise ValueError("Could not generate a unique short_link.")

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(
            **validated_data,
            author=self.context['request'].user,
            short_link=self.generate_short_link()
        )
        self.create_tags(tags, recipe)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.get('tags')
        if tags is None:
            raise serializers.ValidationError(
                {'tags': 'This field is required.'}
            )

        ingredients = validated_data.get('ingredients')
        if ingredients is None:
            raise serializers.ValidationError(
                {'ingredients': 'This field is required.'}
            )

        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_tags(validated_data.pop('tags'), instance)
        self.create_ingredients(validated_data.pop('ingredients'), instance)
        return super().update(instance, validated_data)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент.'
            )

        ingredient_ids = [item['id'] for item in value]
        existing_ids = set(
            Ingredient.objects.filter(id__in=ingredient_ids).values_list(
                'id', flat=True))
        unicum_ids = set()
        for item in value:
            if item['id'] not in existing_ids:
                raise serializers.ValidationError(
                    f"Ингредиент с id={item['id']} не существует.")
            if item['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента не может быть меньше 1.')
            ingredient_id = item['id']
            if ingredient_id in unicum_ids:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.')
            unicum_ids.add(ingredient_id)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один тег.')

        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')

        return value


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')
        read_only_fields = ('user',)


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCartItem
        fields = ('id', 'user', 'recipe')
        read_only_fields = ('user',)


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and Follow.objects.filter(
            follower=user, following=obj
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
