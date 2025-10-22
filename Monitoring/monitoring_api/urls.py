from django.contrib import admin
from django.urls import path, include
from api.metrics_view import metrics
# from rest_framework import permissions
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi

# schema_view = get_schema_view(
#     openapi.Info(
#         title="Analitix API",
#         default_version='v1',
#         description="API documentation for analitix application",
#         terms_of_service="https://www.google.com/policies/terms/",
#         contact=openapi.Contact(email="parsakhezli8304@gmail.com"),
#     ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
# )




urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('metrics/', metrics,),
    path('metrics', metrics,),

    #path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    #path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
