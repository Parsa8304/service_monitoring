from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest


check_total = Counter(
    "monitor_checks_total",
    "Health checks by outcome",
    labelnames=["service", "endpoint_id", "method", "success"],
)

latency_ms = Histogram(
    "monitor_check_latency_ms",
    "Health check latency (ms)",
    labelnames=["service", "endpoint_id", "method"],
    # Good default buckets (in ms). Tweak to your SLOs.
    buckets=(10, 25, 50, 100, 200, 400, 800, 1600, 3200, 6400)
)

def metrics_http_response():
    # Returns raw metrics payload + content type
    return generate_latest(), CONTENT_TYPE_LATEST