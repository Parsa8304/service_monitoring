from rest_framework import serializers
from .models import Service, Endpoint, CheckResult


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'url', 'status', 'last_checked']


class EndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endpoint
        fields = [
            'id', 'service', 'url', 'method', 'expected_status',
            'timeout_ms', 'interval_sec', 'headers', 'enabled', 'next_run_at'
        ]
    
    def validate(self, data):
        if data['method'] not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
            raise serializers.ValidationError("Invalid HTTP method.")
        if not data['url'].startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        if data['timeout_ms'] <= 0:
            raise serializers.ValidationError("Timeout must be a positive integer.")
        if data['interval_sec'] <= 15:
            raise serializers.ValidationError("Interval must be a positive integer.")
        return data


class CheckResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckResult
        fields = [
            'id', 'endpoint', 'timestamp', 'status_code',
            'response_time_ms', 'success', 'details'
        ]
