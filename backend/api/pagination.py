# backend/api/pagination.py
from rest_framework.pagination import PageNumberPagination

class RecipePagination(PageNumberPagination):
    # page_size = 6  # или сколько нужно
    max_page_size = 100
    page_size_query_param = 'limit'


