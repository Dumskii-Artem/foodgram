# backend/food/management/commands/delete_ingredients_all.py

from django.core.management.base import BaseCommand
from food.models import Ingredient

class Command(BaseCommand):
    help = 'Удалить все ингредиенты из базы данных'

    def handle(self, *args, **options):
        count, _ = Ingredient.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            f'Удалено ингредиентов: {count}'
        ))
