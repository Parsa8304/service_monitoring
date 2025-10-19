# api/serializers.py
from rest_framework import serializers
from urllib.parse import urlparse
import re
from django.utils import timezone  # only used for read-only fields on the model
from .models import Service, Endpoint, CheckResult

# Accept single-label Docker service names (letters/digits/hyphens)
DOCKER_HOST_RE = re.compile(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$')

def validate_docker_url(value: str) -> str:
    """
    Relaxed URL validator that allows Docker service DNS names (e.g., http://twitter:8000)
    in addition to localhost and IPs.
    """
    v = (value or "").strip()
    p = urlparse(v)
    if p.scheme not in ("http", "https") or not p.netloc:
        raise serializers.ValidationError("URL must start with http:// or https:// and include a host.")
    host = p.hostname or ""
    if host == "localhost":
        return v
    # allow single-label docker hostnames like "twitter" or "khabarfarsi-api"
    if DOCKER_HOST_RE.fullmatch(host):
        return v
    # allow IPs
    try:
        import ipaddress
        ipaddress.ip_address(host)
        return v
    except Exception:
        pass
    raise serializers.ValidationError(
        "Enter a valid URL (docker service names like http://service:port are allowed)."
    )


class ServiceSerializer(serializers.ModelSerializer):
    # Override the model field so we can plug in our relaxed validator
    url = serializers.CharField(validators=[validate_docker_url])

    class Meta:
        model = Service
        fields = ['id', 'name', 'url', 'status', 'last_checked']
        read_only_fields = ['status', 'last_checked']

    def validate(self, data):
        # Normalize URL (remove trailing slash to keep consistency)
        data['url'] = data['url'].strip().rstrip('/')
        return data
    # IMPORTANT: no HTTP requests here. Health/probing happens in Celery or dedicated actions.


class EndpointSerializer(serializers.ModelSerializer):
    # Allow docker-friendly URLs here too
    url = serializers.CharField(validators=[validate_docker_url])

    # Keep methods constrained; adjust if you added choices on the model
    VALID_METHODS = {'GET','POST','PUT','DELETE','PATCH','HEAD','OPTIONS'}

    class Meta:
        model = Endpoint
        fields = [
            'id', 'service', 'url', 'method', 'expected_status',
            'timeout_ms', 'interval_sec', 'headers', 'enabled', 'next_run_at'
        ]
        extra_kwargs = {
            'url': {'help_text': 'Health endpoint URL (e.g. http://service:8000/health)'},
            'interval_sec': {'help_text': 'How often to check (in seconds, min 15s)'},
            'timeout_ms': {'help_text': 'Request timeout in milliseconds'},
        }

    def validate(self, data):
        # Normalize URL and method
        url = (data.get('url') or '').strip().rstrip('/')
        method = (data.get('method') or 'GET').upper()

        if method not in self.VALID_METHODS:
            raise serializers.ValidationError({"method": "Invalid HTTP method."})

        timeout_ms = int(data.get('timeout_ms', 5000))
        interval_sec = int(data.get('interval_sec', 60))

        if timeout_ms <= 0:
            raise serializers.ValidationError({"timeout_ms": "Timeout must be a positive integer."})
        if interval_sec < 15:
            raise serializers.ValidationError({"interval_sec": "Interval must be at least 15 seconds."})

        data['url'] = url
        data['method'] = method
        return data


class CheckResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckResult
        fields = [
            'id', 'endpoint', 'timestamp', 'status_code',
            'response_time_ms', 'success', 'details'
        ]
        read_only_fields = fields
