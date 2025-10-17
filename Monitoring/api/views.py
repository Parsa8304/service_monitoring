import requests, os, datetime
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .serializers import ServiceSerializer, EndpointSerializer, CheckResultSerializer
from .models import Service, Endpoint, CheckResult

PROM_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class EndpointViewSet(viewsets.ModelViewSet):
    queryset = Endpoint.objects.all()
    serializer_class = EndpointSerializer


class CheckResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CheckResult.objects.all()
    serializer_class = CheckResultSerializer











# def prom_query(query:str):
#     try:
#         response = requests.get(f"{PROM_URL}/api/v1/query", params={"query": query}, timeout=5)
#         response.raise_for_status()
#         result = response.json()
#         if result["status"] == "success":
#             return result["data"]["result"]
#         else:
#             return []
#     except requests.RequestException as e:
#         print(f"Error querying Prometheus: {e}")
#         return []


# def prom_query_range(query:str, start:datetime.datetime, end:datetime.datetime, step:str):
#     try:
#         response = requests.get(f"{PROM_URL}/api/v1/query_range", params={
#             "query": query,
#             "start": start.isoformat(),
#             "end": end.isoformat(),
#             "step": step
#         }, timeout=5)
#         response.raise_for_status()
#         result = response.json()
#         if result["status"] == "success":
#             return result["data"]["result"]
#         else:
#             return []
#     except requests.RequestException as e:
#         print(f"Error querying Prometheus range: {e}")
#         return []


# class ServicesView(APIView):
#     def get(self, request):
#         rows = prom_query('label_values(app_http_requests_total, instance)')
#         services = sorted({r["value"][1].split(":")[0] for r in rows})
#         return Response(services)


# class SummaryView(APIView):
    
#     def get(self, request):
#         rps = {
#             s["metric"]["instance"].split(":")[0]: float(s["value"][1])
#             for s in prom_query('sum by (instance)(rate(app_http_requests_total[1m]))')
#         }

#         err = {
#             s["metric"]["instance"].split(":")[0]: float(s["value"][1])
#             for s in prom_query(
#                 '100 * sum by (instance)(rate(app_http_requests_total{status=~"5.."}[5m]))'
#                 ' / sum by (instance)(rate(app_http_requests_total[5m]))'
#             )
#         }

#         p95 = {
#             s["metric"]["instance"].split(":")[0]: float(s["value"][1])
#             for s in prom_query(
#                 'histogram_quantile(0.95, sum by (instance, le)(app_http_request_duration_seconds_bucket))'
#             )
#         }

#         services = sorted(set(rps) | set(err) | set(p95))
#         data = [
#             {
#                 "service": svc,
#                 "rps": round(rps.get(svc, 0.0), 4),
#                 "error_rate_pct": round(err.get(svc, 0.0), 3),
#                 "p95_latency_ms": round(p95.get(svc, 0.0) * 1000, 1),
#             }
#             for svc in services
#         ]
#         return Response(data)

# class TimeseriesView(APIView):
#     """Timeseries data for a service and metric (for charts)."""
#     def get(self, request):
#         service = request.GET.get("service")
#         metric = request.GET.get("metric", "rps")
#         minutes = int(request.GET.get("minutes", "30"))
#         if not service:
#             return Response({"detail": "service required"}, status=status.HTTP_400_BAD_REQUEST)

#         end = int(datetime.datetime.utcnow().timestamp())
#         start = end - minutes * 60

#         if metric == "rps":
#             q = 'sum by (instance)(rate(app_http_requests_total[1m]))'
#         elif metric == "error_rate_pct":
#             q = (
#                 '100 * sum by (instance)(rate(app_http_requests_total{status=~"5.."}[5m]))'
#                 ' / sum by (instance)(rate(app_http_requests_total[5m]))'
#             )
#         elif metric == "p95_latency":
#             q = 'histogram_quantile(0.95, sum by (instance, le)(app_http_request_duration_seconds_bucket))'
#         else:
#             return Response({"detail": "unknown metric"}, status=status.HTTP_400_BAD_REQUEST)

#         result = prom_query_range(q, start, end, step="15s")
#         out = []
#         for s in result:
#             inst = s["metric"].get("instance", "")
#             if inst.split(":")[0] != service:
#                 continue
#             vals = [
#                 [int(float(t)), round(float(v) * (1000 if metric == "p95_latency" else 1), 4)]
#                 for t, v in s["values"]
#             ]
#             out.append({"service": service, "metric": metric, "points": vals})
#         return Response(out)
