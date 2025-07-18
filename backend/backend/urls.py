# backend/urls.py
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from food.views import redirect_by_short_link

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

urlpatterns += [
    path('recipe_<str:short_link>/',
         redirect_by_short_link,
         name='recipe_short_link'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)