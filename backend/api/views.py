import os
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Exists, OuterRef
from django.http import FileResponse
from django_filters.filters import CharFilter
from django_filters.filterset import FilterSet
from django_filters.rest_framework.backends import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.pagination import RecipePagination
from api.serializers import (FollowedUserSerializer, IngredientSerializer,
                             RecipeReadSerializer, RecipeWriteSerializer,
                             ShortRecipeSerializer, TagSerializer,
                             UserWithSubscriptionSerializer)
from food import constants as const
from food.models import (Favorite, Follow, Ingredient, Recipe,
                         RecipeIngredient, ShoppingCartItem, Tag)
from library.shopping_list import generate_shopping_list

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_permissions(self):
        print(f'get_permissions: request method: {self.request.method}')
        if self.request.method in ['PATCH', 'POST', 'PUT', 'DELETE']:
            # Для изменений — только аутентифицированный пользователь
            # permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
            permission_classes = [IsAuthenticated]
        else:
            # Для остальных — разрешаем и анонимным (только чтение)
            permission_classes = [IsAuthenticatedOrReadOnly]
        s = [permission() for permission in permission_classes]
        print(f'get_permissions: permission_classes: {permission_classes} {s}')
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        is_in_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_cart and user.is_authenticated:
            cart_subquery = ShoppingCartItem.objects.filter(
                user=user,
                recipe=OuterRef('pk')
            )
            queryset = queryset.annotate(
                in_cart=Exists(cart_subquery)
            ).filter(in_cart=True)

        return queryset

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        self.get_object()
        short_link = f'{const.RECIPE_SHORT_LINK}{pk}'
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[AllowAny]
    )
    def set_image(self, request):
        recipe = request.recipe
        image = request.data.get('image')

        if not image:
            return Response(
                {'image': ['Это поле обязательно.']},
                status=status.HTTP_400_BAD_REQUEST)

        # Сохраняем текущий путь старого аватара (если есть)
        old_image_path = recipe.image.path if recipe.image else None

        # Создаем новый файл аватара, не удаляя пока старый
        recipe.image = (
            RecipeReadSerializer().fields['image'].to_internal_value(image))
        recipe.save()

        # Удаляем старый файл, если он был и отличается от нового
        if old_image_path and os.path.isfile(old_image_path):
            try:
                # Проверяем, что новый файл не совпадает с удаляемым
                if old_image_path != recipe.image.path:
                    os.remove(old_image_path)
            except Exception:
                # На всякий случай подавляем ошибку удаления,
                # чтобы не ломать ответ
                pass

        return Response(
            {'image': recipe.image.url if recipe.image else None},
            status=status.HTTP_200_OK
        )

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user

        recipe_ids = ShoppingCartItem.objects.filter(user=user).values_list(
            'recipe_id', flat=True)
        recipes = Recipe.objects.filter(id__in=recipe_ids)

        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=models.Sum('amount'))
            .order_by('ingredient__name')
        )

        content = generate_shopping_list(user, ingredients, recipes)

        buffer = BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain'
        )

    def handle_add_or_remove(self, model, user, recipe, request,
                             serializer_class=None):
        obj = model.objects.filter(user=user, recipe=recipe)

        if request.method == 'POST':
            if obj.exists():
                return Response({'error': 'Объект уже существует'},
                                status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=user, recipe=recipe)
            serializer = serializer_class(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not obj.exists():
                return Response({'error': 'Объекта нет'},
                                status=status.HTTP_400_BAD_REQUEST)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated]
            )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return self.handle_add_or_remove(
            model=ShoppingCartItem,
            request=request,
            user=request.user,
            recipe=recipe,
            serializer_class=ShortRecipeSerializer
        )

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated]
            )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return self.handle_add_or_remove(
            model=Favorite,
            request=request,
            user=request.user,
            recipe=recipe,
            serializer_class=ShortRecipeSerializer
        )

    def get_object(self):
        obj = super().get_object()
        print(f'get_object: obj: {obj}')

        # Если метод изменения и не автор — явно вернуть 403
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            if obj.author != self.request.user:
                raise PermissionDenied('Нельзя редактировать чужой рецепт.')
        return obj


class UserWithSubscriptionViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserWithSubscriptionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        print('set_avatar: Request data:', request.data)
        user = request.user

        if request.method == 'PUT':
            avatar = request.data.get('avatar')
            if not avatar:
                raise ValidationError({'avatar': ['Это поле обязательно.']})

            user.avatar = UserWithSubscriptionSerializer(
                context={'request': request}
            ).fields['avatar'].to_internal_value(avatar)

            user.save()

            return Response(
                {'avatar': user.avatar.url if user.avatar else None},
                status=status.HTTP_200_OK)

        # elif request.method == 'DELETE':
        if (
                user.avatar
                and user.avatar.path
                and os.path.isfile(user.avatar.path)
        ):
            try:
                os.remove(user.avatar.path)
            except Exception:
                pass  # подавляем ошибки удаления

        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated]
            )
    def subscribe(self, request, **kwargs):
        pk = kwargs.get('id')
        user = request.user

        if request.method == 'POST':
            author = get_object_or_404(User, pk=pk)

            if user.id == author.id:
                raise ValidationError('Нельзя подписаться на самого себя')

            if Follow.objects.filter(follower=user, author=author).exists():
                raise ValidationError('Вы уже подписаны на этого пользователя')

            Follow.objects.create(follower=user, author=author)

            serializer = FollowedUserSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # if request.method == 'DELETE':
        author = get_object_or_404(User, id=pk)
        try:
            Follow.objects.get(follower=request.user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response(
                {'error': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def subscriptions(self, request):
        authors = User.objects.filter(
            pk__in=Follow.objects
            .filter(follower=request.user)
            .values_list('author__id', flat=True)
        )
        paginator = RecipePagination()
        page = paginator.paginate_queryset(authors, request)
        serializer = FollowedUserSerializer(
            page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)
