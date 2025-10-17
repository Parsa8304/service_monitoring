from django.urls import path, include
from .views import ServiceViewSet, EndpointViewSet, CheckResultViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'endpoints', EndpointViewSet, basename='endpoint')
router.register(r'checkresults', CheckResultViewSet, basename='checkresult')

urlpatterns = [
    path('', include(router.urls)),
]
