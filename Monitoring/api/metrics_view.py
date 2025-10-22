from django.http import HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, CollectorRegistry
from prometheus_client import multiprocess


def metrics(request):
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    output = generate_latest(registry)
    return HttpResponse(output, content_type=CONTENT_TYPE_LATEST)
