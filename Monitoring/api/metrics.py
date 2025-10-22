from prometheus_client import Counter, Histogram

check_total = Counter(
    "monitor_checks_total", "Total number of checks",
    ["service", "endpoint_id", "method", "success"]
)

latency_ms = Histogram(
    "monitor_check_latency_ms", "Latency of checks in ms",
    ["service", "endpoint_id", "method"]
)

response_status = Counter(
    "monitor_check_response_status", "Response status codes from checks",
    ["service", "endpoint_id", "method", "status_code"]
)
