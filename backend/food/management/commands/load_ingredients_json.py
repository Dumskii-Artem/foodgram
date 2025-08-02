from food.models import Ingredient

from .base_load_command import BaseLoadCommand


class Command(BaseLoadCommand):
    model = Ingredient
