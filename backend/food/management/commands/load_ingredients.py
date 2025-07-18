# backend/food/management/commands/load_ingredients.py

import csv
from django.core.management.base import BaseCommand
from food.models import Ingredient

class Command(BaseCommand):
    help = 'Загружает ингредиенты из CSV-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к CSV-файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        created_count = 0
        with open(file_path, encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 2:
                    continue  # пропустить неполные строки
                name, unit = row
                obj, created = Ingredient.objects.get_or_create(
                    name=name.strip(),
                    measurement_unit=unit.strip()
                )
                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Загружено ингредиентов: {created_count}'
        ))