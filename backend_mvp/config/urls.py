from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.orders.urls')),
    path('api/v1/', include('apps.responses.urls')),
    path('api/v1/', include('apps.deals.urls')),
    path('api/v1/', include('apps.reviews.urls')),
    path('api/v1/', include('apps.ratings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
