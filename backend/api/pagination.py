from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    page_size = 6
    max_page_size = 100
    page_size_query_param = 'limit'
