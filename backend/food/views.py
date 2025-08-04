from django.http import Http404
from django.shortcuts import redirect

from food.models import Recipe


def short_link_redirect_view(request, pk):
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404(f'Рецепт с id={pk} не найден.')
    return redirect(f'/recipes/{pk}/')
