from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('presentation.webhook.urls')),
    path('api/', include('presentation.api.urls')),
]
