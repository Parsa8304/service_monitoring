# api/checks.py
import asyncio
import logging
import random
import time

import httpx
from django.db import transaction
from django.utils import timezone

from .models import Endpoint, CheckResult, Service
from .metrics import check_total, latency_ms, response_status

log = logging.getLogger(__name__)

# Tunables
MAX_CONCURRENCY = 20
RETRY_COUNT = 1                 # one retry after a short backoff
BACKOFF_BASE_S = 0.2            # base backoff between retries
SCHED_JITTER_S = 0.5            # small jitter when scheduling next_run_at to avoid herding


def _now_ms() -> int:
    return int(time.time() * 1000)


def _labels_for(ep: Endpoint) -> dict:
    return {"service": ep.service.name, "endpoint_id": str(ep.id), "method": ep.method}


async def _probe(client: httpx.AsyncClient, ep: Endpoint):
    """
    Single probe attempt. Returns tuple:
    (ok: bool, status_code: int, elapsed_ms: int, details: str)
    """
    start = _now_ms()
    try:
        # Normalize/guard inputs per attempt
        method = (ep.method or "GET").upper()
        timeout_s = max(0.001, (ep.timeout_ms or 5000) / 1000.0)

        r = await client.request(
            method,
            ep.url,
            headers=ep.headers or {},
            timeout=httpx.Timeout(timeout_s),
            follow_redirects=True,
        )
        elapsed = _now_ms() - start
        ok = (r.status_code == (ep.expected_status or 200))
        if not ok:
            return False, r.status_code, elapsed, f"Expected {ep.expected_status} got {r.status_code}"
        return True, r.status_code, elapsed, ""
    except Exception as e:
        elapsed = _now_ms() - start
        return False, 0, elapsed, str(e)


async def _probe_with_retry(client: httpx.AsyncClient, ep: Endpoint):
    ok, code, rtt, details = await _probe(client, ep)
    if not ok and RETRY_COUNT > 0:
        await asyncio.sleep(BACKOFF_BASE_S + random.random() * 0.3)
        ok2, code2, rtt2, details2 = await _probe(client, ep)
        # Prefer the second attempt’s data; fall back to the first where missing
        ok, code, rtt, details = ok2, (code2 or code), (rtt2 or rtt), (details2 or details)
    return ok, code, rtt, details


async def _fetch_results(endpoints):
    """
    Run all probes concurrently with a connection limit.
    """
    limits = httpx.Limits(max_connections=MAX_CONCURRENCY)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [_probe_with_retry(client, ep) for ep in endpoints]
        return await asyncio.gather(*tasks)


def run_due_checks() -> int:
    """
    Synchronous entrypoint (safe for Celery workers):
      1) Read due endpoints (sync ORM)
      2) Probe concurrently (async httpx via asyncio.run)
      3) Persist results + schedule next runs (sync ORM)
      4) Update service statuses (simple aggregation)
    """
    # ---- 1) SYNC ORM: select due endpoints
    due = list(
        Endpoint.objects.select_related("service")
        .filter(enabled=True, next_run_at__lte=timezone.now())
        .order_by("next_run_at")[:500]
    )
    if not due:
        return 0

    # ---- 2) ASYNC IO: probe concurrently
    try:
        results = asyncio.run(_fetch_results(due))
    except RuntimeError:
        # If we're somehow already inside a running loop (shouldn't happen in Celery),
        # create a fresh loop explicitly.
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(_fetch_results(due))
        finally:
            loop.close()

    # ---- 3) SYNC ORM: persist results + schedule next runs
    with transaction.atomic():
        touched_service_ids = set()

        for ep, (ok, code, rtt, details) in zip(due, results):
            # Prometheus metrics
            labels = {"service": ep.service.name, "endpoint_id": str(ep.id), "method": ep.method}
            check_total.labels(**labels, success="true" if ok else "false").inc()
            latency_ms.labels(**labels).observe(float(rtt))
            response_status.labels(**labels, status_code=str(code or 0)).inc()

            # DB row
            CheckResult.objects.create(
                endpoint=ep,
                status_code=code or 0,
                response_time_ms=int(rtt),
                success=bool(ok),
                details=(details[:2000] if details else None),
            )

            # Schedule next run (with jitter)
            next_run = timezone.now() + timezone.timedelta(seconds=max(1, ep.interval_sec or 60))
            if SCHED_JITTER_S:
                next_run += timezone.timedelta(seconds=random.uniform(0, SCHED_JITTER_S))
            ep.next_run_at = next_run
            ep.save(update_fields=["next_run_at"])

            touched_service_ids.add(ep.service_id)


        # ---- 4) Update service statuses (simple rule over last N checks)
        for sid in touched_service_ids:
            svc = Service.objects.get(pk=sid)
            last10 = list(
                CheckResult.objects.filter(endpoint__service=sid).order_by("-timestamp")[:10]
            )
            svc.status = "UNHEALTHY" if any(not c.success for c in last10) else "HEALTHY"
            svc.last_checked = timezone.now()
            svc.save(update_fields=["status", "last_checked"])

    return len(due)
