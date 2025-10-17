from django.urls import path
from .views import producthunt_filter, health_check

urlpatterns = [
    path('filter/', producthunt_filter, name='producthunt_filter'),
    path('health/', health_check, name='health_check'), # added by Parsa for health check
]