# backend/food/models.py
from django.core.validators import MinValueValidator
from django.db import models
from food import constants as const
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=const.TAG_NAME_LENGTH,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=const.TAG_SLUG_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=const.INGREDIENT_NAME_LENGTH,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=const.INGREDIENT_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        help_text='Количество ингредиента в рецепте'
    )

    class Meta:
        unique_together = ('recipe', 'ingredient')
        verbose_name = 'Количество ингредиента'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=const.RECIPE_NAME_LENGTH,
        verbose_name='Название рецепта',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение рецепта',
        help_text='Загрузите изображение рецепта'
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(const.RECIPE_MIN_COOKING_TIME)],
        verbose_name="Время приготовления (мин)"
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=False,
        through='RecipeTag',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        blank=False,
        through='RecipeIngredient',
        related_name='recipes'
    )
    short_link = models.CharField(
        max_length=6,
        unique=True,
        editable=False,
        blank=False,
        null=False
    )

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_tags',
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='tag_recipe',
        verbose_name='Тег'
    )

    class Meta:
        unique_together = ('recipe', 'tag')
        verbose_name = 'Тег рецепта'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в избранное "{self.recipe}"'


class ShoppingCartItem(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart_item'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в корзину "{self.recipe}"'