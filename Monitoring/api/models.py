from django.db import models


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField()
    status = models.CharField(max_length=50)
    last_checked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Endpoint(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='endpoint')
    url = models.CharField(max_length=200)
    method = models.CharField(default='GET', max_length=10)
    expected_status = models.IntegerField(default=200)
    timeout_ms = models.IntegerField(default=5000)
    interval_sec = models.IntegerField(default=60)
    headers = models.JSONField(blank=True, null=True)
    enabled = models.BooleanField(default=True)
    next_run_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.service.name} - {self.url}"


class CheckResult(models.Model):
    endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE, related_name='check_results')
    timestamp = models.DateTimeField(auto_now_add=True)
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField()
    success = models.BooleanField()
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.endpoint.service.name} - {self.timestamp} - {'Success' if self.success else 'Failure'}"
