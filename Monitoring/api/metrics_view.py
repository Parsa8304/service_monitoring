from django.http import HttpResponse
from .metrics import metrics_http_response

def metrics(request):
    data, ctype = metrics_http_response()
    return HttpResponse(data, content_type=ctype)
