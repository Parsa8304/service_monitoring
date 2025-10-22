import os, httpx
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Service, Endpoint, CheckResult
from .serializers import ServiceSerializer, EndpointSerializer, CheckResultSerializer

REG_TOKEN = os.getenv("MONITOR_REGISTRATION_TOKEN", "change-me")


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        svc = self.get_object()
        return Response({
            "service": ServiceSerializer(svc).data,
            "endpoints": EndpointSerializer(svc.endpoint.all(), many=True).data,
        })


class EndpointViewSet(viewsets.ModelViewSet):
    queryset = Endpoint.objects.select_related("service").all()
    serializer_class = EndpointSerializer

    @action(detail=True, methods=["post"])
    def probe(self, request, pk=None):
        ep = self.get_object()
        try:
            r = httpx.request(ep.method, ep.url, headers=ep.headers or {}, timeout=ep.timeout_ms/1000.0)
            ok = (r.status_code == ep.expected_status)
            return Response(
                {"status_code": r.status_code, "ok": ok, "expected": ep.expected_status},
                status=status.HTTP_200_OK if ok else status.HTTP_424_FAILED_DEPENDENCY,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=424)


class CheckResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CheckResult.objects.select_related("endpoint", "endpoint__service").all()
    serializer_class = CheckResultSerializer
    ordering = ["-timestamp"]


class RegisterServiceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.headers.get("X-Registration-Token") or request.data.get("token")
        if token != REG_TOKEN:
            return Response({"detail": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        name = request.data.get("name")
        base_url = request.data.get("base_url")
        if not name or not base_url:
            return Response({"detail": "name and base_url required"}, status=status.HTTP_400_BAD_REQUEST)

        svc, _ = Service.objects.update_or_create(
            name=name,
            defaults={"url": base_url, "last_checked": timezone.now()},
        )

        default_url = base_url.rstrip("/") + "/health"
        Endpoint.objects.get_or_create(
            service=svc,
            url=default_url,
            method="GET",
            defaults={
                "expected_status": 200,
                "timeout_ms": 3000,
                "interval_sec": 60,
                "enabled": True},
        )

        return Response({"detail": "registered", "service_id": svc.id})
