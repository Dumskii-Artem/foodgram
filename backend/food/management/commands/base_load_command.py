# backend/food/management/commands/base_load_command.py

# не тестировал !!!
# python manage.py load_ingredients_json ../data/ingredients.json
# python manage.py load_tags_json ../data/tags.json

import json

from django.core.management.base import BaseCommand


class BaseLoadCommand(BaseCommand):
    model = None  # установить в дочернем классе
    fields = []   # список полей для модели

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON-файлу'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            with open(file_path, encoding='utf-8') as file:
                data = json.load(file)

            seen = set()
            for item in data:
                key = tuple(item[field] for field in self.fields)
                if len(key) != len(self.fields):
                    print(f"Пропущено: {item} — несовпадение количества полей")
                    continue
                seen.add(key)

            objects = [
                self.model(**dict(zip(self.fields, values)))
                for values in seen
            ]

            self.model.objects.bulk_create(objects, ignore_conflicts=True)

            self.stdout.write(self.style.SUCCESS(
                f'Загружено записей: {len(objects)}'
            ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка: {str(e)}'))
