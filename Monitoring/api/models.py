from django.db import models
from django.utils import timezone


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField()
    status = models.CharField(max_length=50, blank=True, null=True)
    last_checked = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class Endpoint(models.Model):

    METHOD_CHOICES = {
        'GET': 'get',
        'POST': 'post',
        'PUT': 'put',
        'DELETE': 'delete',
        'PATCH': 'patch',
        'HEAD': 'head',
        'OPTIONS': 'options'
    }

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='endpoint')
    url = models.URLField(max_length=200)
    method = models.CharField(default='GET', choices=METHOD_CHOICES, max_length=10)
    expected_status = models.IntegerField(default=200)
    timeout_ms = models.IntegerField(default=5000)
    interval_sec = models.IntegerField(default=60)
    headers = models.JSONField(blank=True, null=True)
    enabled = models.BooleanField(default=True)
    next_run_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ('service', 'url', 'method')
        indexes = [
            models.Index(fields=['service', 'enabled', 'next_run_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.next_run_at:
            self.next_run_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service.name} - {self.url}"


class CheckResult(models.Model):
    endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE, related_name='check_results')
    timestamp = models.DateTimeField(auto_now_add=True)
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField()
    success = models.BooleanField()
    details = models.TextField(blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['endpoint', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.endpoint.service.name} - {self.timestamp} - {'Success' if self.success else 'Failure'}"
