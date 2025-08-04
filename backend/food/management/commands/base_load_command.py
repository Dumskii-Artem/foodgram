# запускать команды для загрузки данных можно так:
# python manage.py load_ingredients_json ../data/ingredients.json
# python manage.py load_tags_json ../data/tags.json

import json

from django.core.management.base import BaseCommand


class BaseLoadCommand(BaseCommand):
    model = None  # установить в дочернем классе

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON-файлу'
        )

    class Command(BaseCommand):
        help = 'Импорт данных из JSON-файла'

    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            with open(file_path, encoding='utf-8') as file:
                created = self.model.objects.bulk_create(
                    (self.model(**item) for item in json.load(file)),
                    ignore_conflicts=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Добавлено {len(created)}'
                        f' объектов из файла "{file_path}"'
                    )
                )
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f'Ошибка при обработке файла {file_path}: {e}'
            ))
