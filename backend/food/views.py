# backend/food/views.py
import os

from django.db.models import OuterRef, Exists
from django.http import HttpResponse
from django.shortcuts import redirect
from django_filters.filters import CharFilter
from django_filters.filterset import FilterSet
from django.db import models
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from .filters import RecipeFilter
from .models import Tag, Ingredient, Recipe, Favorite, ShoppingCartItem, \
    RecipeIngredient
from .permissions import IsAuthorOrReadOnly
from .serializers import TagSerializer, IngredientSerializer, \
    RecipeWriteSerializer, RecipeReadSerializer, FavoriteSerializer, \
    ShoppingCartSerializer, RecipeShortSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated, \
    IsAuthenticatedOrReadOnly

from food import constants as const

def redirect_by_short_link(request, short_link):
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(f'{const.RECIPE_FRONT_SHORT_LINK}{recipe.id}')


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

#
# class RecipeSerializer:
#     pass
#

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    # serializer_class = RecipeSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['tags']  # твои фильтры, например теги
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.request.method in ['PATCH', 'POST', 'PUT', 'DELETE']:
            # Для изменений — только аутентифицированный пользователь
            permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
        else:
            # Для остальных — разрешаем и анонимным (только чтение)
            permission_classes = [IsAuthenticatedOrReadOnly]
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
        recipe = self.get_object()
        short_link = f'{const.RECIPE_BACK_SHORT_LINK}{recipe.short_link}'
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        # ❗️ Отдаём сериализованный объект с READ-сериализатором
        read_serializer = RecipeReadSerializer(
            recipe,
            context={'request': request}
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        # print(f'shopping_cart: User: {user}, Recipe ID: {pk}')
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if ShoppingCartItem.objects.filter(user=user, recipe=recipe).exists():
                return Response({'error': 'Рецепт уже в корзине'}, status=status.HTTP_400_BAD_REQUEST)

            ShoppingCartItem.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            cart_item = ShoppingCartItem.objects.filter(user=user, recipe=recipe)
            if cart_item.exists():
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Рецепта нет в корзине'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(
            id__in=ShoppingCartItem.objects.filter(user=request.user)
            .values_list('recipe_id', flat=True)
        )

        ingredients = (RecipeIngredient.objects
                       .filter(recipe__in=recipes)
                       .values('ingredient__name',
                               'ingredient__measurement_unit')
                       .annotate(total_amount=models.Sum('amount'))
                       .order_by('ingredient__name'))

        lines = []
        for item in ingredients:
            line = f"{item['ingredient__name']} ({item['ingredient__measurement_unit']}) — {item['total_amount']}"
            lines.append(line)

        content = '\n'.join(lines)
        filename = 'shopping_list.txt'

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже в избранном.'}, status=status.HTTP_400_BAD_REQUEST)

            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite.exists():
                return Response({'errors': 'Рецепт не в избранном.'}, status=status.HTTP_400_BAD_REQUEST)

            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.request.data.get('recipe'))
        serializer.save(user=self.request.user, recipe=recipe)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCartItem.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return ShoppingCartItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.request.data.get('recipe'))
        serializer.save(user=self.request.user, recipe=recipe)