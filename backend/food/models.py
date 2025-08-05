from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from food import constants as const

username_validator = RegexValidator(
    regex=r'^[\w.@-]+$',
    message=('Имя пользователя может содержать'
             ' только буквы, цифры и символы @ . - _')
)


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=const.USER_EMAIL_LENGTH,
        verbose_name='Электронная почта',
    )
    first_name = models.CharField(
        max_length=const.USER_FIRST_NAME_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=const.USER_LAST_NAME_LENGTH,
        verbose_name='Фамилия'
    )
    username = models.CharField(
        max_length=const.USER_USERNAME_LENGTH,
        unique=True,
        verbose_name='Логин',
        validators=[username_validator],
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        # все пользователи, подписанные на этого автора
        related_name='author_followes',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    follower = models.ForeignKey(
        User,
        # все авторы, на которых подписан этот пользователь
        related_name='follower_followes',
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'follower'],
                name='unique_author_follower'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.follower} подписан на {self.author}'


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
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=const.INGREDIENT_NAME_LENGTH,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=const.INGREDIENT_MEASUREMENT_UNIT_LENGTH,
        verbose_name='единица измерения'
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=const.RECIPE_NAME_LENGTH,
        verbose_name='Название',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение',
        help_text='Загрузите изображение рецепта'
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(const.RECIPE_MIN_COOKING_TIME)],
        verbose_name='Время (мин)'
    )
    tags = models.ManyToManyField(
        'Tag',
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        related_name='recipes'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-id']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipe',
        verbose_name='Продукт'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Мера',
        help_text='Мера продукта в рецепте'
    )

    class Meta:
        verbose_name = 'Продукт в рецепте'
        verbose_name_plural = 'Продукты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class UserRecipeRelationBase(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)ss'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='%(class)ss'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe}'


class Favorite(UserRecipeRelationBase):
    class Meta(UserRecipeRelationBase.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCartItem(UserRecipeRelationBase):
    class Meta(UserRecipeRelationBase.Meta):
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Корзина покупок'
