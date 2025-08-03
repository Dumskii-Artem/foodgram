import os

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Exists, OuterRef
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import now
from django_filters.filters import CharFilter
from django_filters.filterset import FilterSet
from django_filters.rest_framework.backends import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.pagination import RecipePagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (FollowedUserSerializer, FoodgramUserSerializer,
                             IngredientSerializer, RecipeReadSerializer,
                             RecipeWriteSerializer, ShortRecipeSerializer,
                             TagSerializer)
from food.models import (Favorite, Follow, Ingredient, Recipe,
                         RecipeIngredient, ShoppingCartItem, Tag)

User = get_user_model()


def short_link_redirect_view(request, pk):
    get_object_or_404(Recipe, pk=pk)
    # frontend_url = f'http://localhost:3000/recipes/{pk}/'
    # frontend_url = f'https://babybear.myddns.me/recipes/{pk}/'
    # frontend_url = f'/recipes/{pk}/'
    return HttpResponseRedirect(f'/recipes/{pk}/')


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

    # permission_classes = [IsAuthenticatedOrReadOnly]
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

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

        return queryset.order_by('id')

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        # Просто проверим, что рецепт существует
        if not Recipe.objects.filter(pk=pk).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        relative_url = reverse('recipe-short-link', kwargs={'pk': pk})
        short_link = request.build_absolute_uri(relative_url)

        return Response({'short-link': short_link},
                        status=status.HTTP_200_OK)

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
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        recipes = Recipe.objects.filter(
            id__in=ShoppingCartItem.objects.filter(user=user).values_list(
                'recipe_id', flat=True)
        )

        content = render_to_string('shopping_list.txt', {
            'user': user,
            'date': now().date(),
            'ingredients': (
                RecipeIngredient.objects
                .filter(recipe__in=recipes)
                .values('ingredient__name', 'ingredient__measurement_unit')
                .annotate(total_amount=models.Sum('amount'))
                .order_by('ingredient__name')
            ),
            'recipes': recipes,
        })

        response = HttpResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    def handle_add_or_remove(self, model, user, recipe_id, request):

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=recipe_id)
            obj, created = model.objects.get_or_create(user=user,
                                                       recipe=recipe)
            if not created:
                return Response({'error': 'Объект уже существует'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = ShortRecipeSerializer(recipe,
                                               context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            obj = get_object_or_404(model, user=user, recipe_id=recipe_id)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # print('Метод не поддерживается')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.handle_add_or_remove(
            model=ShoppingCartItem,
            request=request,
            user=request.user,
            recipe_id=pk
        )

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.handle_add_or_remove(
            model=Favorite,
            recipe_id=pk,
            request=request,
            user=request.user
        )


class UserWithSubscriptionViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = FoodgramUserSerializer
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
        user = request.user

        if request.method == 'PUT':
            avatar = request.data.get('avatar')
            if not avatar:
                raise ValidationError({'avatar': ['Это поле обязательно.']})

            user.avatar = FoodgramUserSerializer(
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
        pk = kwargs['id']
        user = request.user

        if request.method == 'DELETE':
            get_object_or_404(Follow,
                              follower=request.user,
                              author_id=pk
                              ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # if request.method == 'POST':
        author = get_object_or_404(User, pk=pk)

        if user.id == author.id:
            raise ValidationError('Нельзя подписаться на самого себя')

        obj, created = Follow.objects.get_or_create(follower=user,
                                                    author=author)
        if not created:
            raise ValidationError(
                f'Вы уже подписаны на пользователя {author.username}')

        serializer = FollowedUserSerializer(
            author,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
