# backend/library/shopping_list.py

from django.template.loader import render_to_string
from django.utils.timezone import now

def generate_shopping_list(user, ingredients, recipes):
    """
    Возвращает текстовый список покупок, сформированный из шаблона.
    """
    return render_to_string('shopping_list.txt', {
        'user': user,
        'date': now().date(),
        'ingredients': ingredients,
        'recipes': recipes,
    })