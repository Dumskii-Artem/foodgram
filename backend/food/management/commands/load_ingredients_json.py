# backend/food/management/commands/load_ingredients_json.py

from food.models import Ingredient

from .base_load_command import BaseLoadCommand


class Command(BaseLoadCommand):
    help = 'Загружает ингредиенты из JSON-файла'
    model = Ingredient
    fields = ['name', 'measurement_unit']
