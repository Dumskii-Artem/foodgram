from food.models import Tag

from .base_load_command import BaseLoadCommand


class Command(BaseLoadCommand):
    model = Tag
