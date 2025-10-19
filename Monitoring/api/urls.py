from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, EndpointViewSet, CheckResultViewSet, RegisterServiceView

router = DefaultRouter()
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"endpoints", EndpointViewSet, basename="endpoint")
router.register(r"results", CheckResultViewSet, basename="result")

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterServiceView.as_view(), name="register-service"),
]
