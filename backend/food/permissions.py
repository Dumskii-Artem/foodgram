# backend/food/permissions.py

from rest_framework.permissions import IsAuthenticatedOrReadOnly, SAFE_METHODS
from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )