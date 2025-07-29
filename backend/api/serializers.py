# backend/api/serializers.py
import uuid

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from rest_framework import serializers

from food.models import (Favorite, Follow, Ingredient, Recipe,
                         RecipeIngredient, ShoppingCartItem, Tag)
from library.base64ImageField import Base64ImageField

User = get_user_model()


class UserWithSubscriptionSerializer(UserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('avatar', 'is_subscribed')
        read_only_fields = fields

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (request
                and not request.user.is_anonymous
                and request.user.followers.filter(author=author).exists())


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
    # amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    # id = serializers.IntegerField()
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        label='Ингредиент',
        source='ingredient'
    )
    amount = serializers.IntegerField(
        min_value=1,
        label='Количество'
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
    author = UserWithSubscriptionSerializer()
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
        user = self.context.get('request')
        return bool(
            user
            and user.user.is_authenticated
            and model_class.objects.filter(
                user=user.user, recipe=recipe
            ).exists()
        )

    def get_is_favorited(self, recipe):
        return self.check_user_status(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self.check_user_status(recipe, ShoppingCartItem)


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
    cooking_time = serializers.IntegerField(
        min_value=1,
        label='Время приготовления (минуты)',
        error_messages={
            'min_value': 'Время приготовления не может быть меньше 1 минуты.'
        }
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
            # context={'request': self.context['request']}
        ).data

    def create_ingredients(self, ingredients, recipe):
        print(f'create_ingredients ingredients={ingredients}, recipe={recipe}')
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['ingredient'].id,
                amount=item['amount']
            )
            for item in ingredients
        ]
        print(f'create_ingredients recipe_ingredients={recipe_ingredients}')
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def generate_short_link(self):
        for _ in range(10):  # 10 попыток
            short_id = uuid.uuid4().hex[:6]
            if not Recipe.objects.filter(short_link=short_id).exists():
                return short_id
        raise ValueError("Could not generate a unique short_link.")

    def create(self, validated_data):
        print(f'validated_data={validated_data}')
        ingredients = validated_data.pop('ingredients')
        print(f'ingredients={ingredients}')
        tags = validated_data.pop('tags')

        validated_data['author'] = self.context['request'].user
        recipe = super().create(validated_data)

        recipe.author = self.context['request'].user
        # recipe.short_link = self.generate_short_link()
        recipe.save()
        recipe.tags.set(tags)
        # self.create_tags(tags, recipe)
        self.create_ingredients(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        instance.ingredients_in_recipe.all().delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()

        required_fields = ['ingredients', 'tags']
        missing_fields = {
            field: 'Это поле обязательно при обновлении рецепта.'
            for field in required_fields if field not in validated_data
        }
        if missing_fields:
            raise serializers.ValidationError(missing_fields)

        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        instance.ingredients_in_recipe.all().delete()
        self.create_ingredients(ingredients, instance)

        return super().update(instance, validated_data)

    @staticmethod
    def find_duplicates(items, key):
        # print(f'find_duplicates items={items}, key={key}')
        seen = set()
        duplicates = set()

        for item in items:
            if isinstance(item, dict):
                identifier = item[key]
            else:
                identifier = getattr(item, key)

            if identifier in seen:
                duplicates.add(identifier)
            seen.add(identifier)

        return duplicates

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент.')
        # print(f'validate_ingredients ingredients={ingredients}')
        duplicate_ids = self.find_duplicates(ingredients, 'ingredient')
        # print(f'validate_ingredients duplicate_ids={duplicate_ids}')
        if duplicate_ids:
            duplicate_ids_int = [
                item.id if hasattr(item, 'id') else item
                for item in duplicate_ids
            ]
            names = Ingredient.objects.filter(
                id__in=duplicate_ids_int).values_list('name', flat=True)
            raise serializers.ValidationError(
                f'Ингредиенты не должны повторяться: {", ".join(names)}.')

        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один тег.')

        duplicate_ids = self.find_duplicates(tags, key='id')
        if duplicate_ids:
            names = (Tag.objects.filter(id__in=duplicate_ids)
                     .values_list('name', flat=True))
            raise serializers.ValidationError(
                f'Теги не должны повторяться: {", ".join(names)}.'
            )

        return tags


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
        read_only_fields = fields

# class RecipeShortSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Recipe
#         fields = ('id', 'name', 'image', 'cooking_time')


class FollowedUserSerializer(UserSerializer):
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count',
        )
        read_only_fields = fields

    def get_is_subscribed(self, followed_user):
        user = self.context['request'].user
        return user.is_authenticated and Follow.objects.filter(
            follower=user, author=followed_user
        ).exists()

    def get_recipes(self, obj):
        limit = int(self.context['request'].GET.get('recipes_limit', 10 ** 10))
        return ShortRecipeSerializer(
            obj.recipes.all()[:limit],
            many=True,
            context=self.context
        ).data
