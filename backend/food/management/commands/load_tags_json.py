# backend/food/management/commands/load_tags_json.py

from food.models import Tag

from .base_load_command import BaseLoadCommand


class Command(BaseLoadCommand):
    help = 'Загружает теги из JSON-файла'
    model = Tag
    fields = ['name', 'slug']
