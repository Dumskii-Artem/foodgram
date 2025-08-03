from django.http import HttpResponseRedirect
from rest_framework.generics import get_object_or_404

from food.models import Recipe


def short_link_redirect_view(request, pk):
    get_object_or_404(Recipe, pk=pk)
    # frontend_url = f'http://localhost:3000/recipes/{pk}/'
    # frontend_url = f'https://babybear.myddns.me/recipes/{pk}/'
    # frontend_url = f'/recipes/{pk}/'
    return HttpResponseRedirect(f'/recipes/{pk}/')
