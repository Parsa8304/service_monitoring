from django.contrib import admin
from django.urls import path, include
from api.metrics_view import metrics


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('metrics/', metrics, name='metrics'),

]
