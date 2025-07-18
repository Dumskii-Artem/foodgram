# backend/users/pagination.py
from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 6  # или сколько нужно
    page_size_query_param = 'limit'