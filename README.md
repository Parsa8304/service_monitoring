# 🩺 API Uptime Monitor

A **Django REST Framework (DRF)**-based monitoring system that checks if your APIs are up, healthy, and performing well.

This project is designed to **scale easily** — you can add or remove monitored APIs without changing the code.  
It works by periodically pinging registered health endpoints (from FastAPI, Django, or any other service) and storing their results.

---

## 🚀 Features

- **API health monitoring** — ping any number of APIs and record response time & status.
- **Manual service registration (v1)** — register new APIs via the REST API or Django admin.
- **Scalable architecture** — adding new APIs doesn’t require code changes.
- **Persistent results** — every check is saved with latency, HTTP code, and error info.
- **Service-level summaries** — see current status, uptime %, and p95 latency.
- **Pluggable scheduler** — supports APScheduler (simple) or Celery (distributed).
- **Alert hooks (future)** — send notifications on state changes (up/down).

---

## 🧩 Architecture Overview

arduino
Copy code
      ┌──────────────────────┐
      │   Django + DRF API   │
      │ (stores services &   │
      │  endpoints)          │
      └─────────┬────────────┘
                │
    ┌───────────▼───────────┐
    │     Scheduler/Worker  │
    │ (APScheduler or Celery│
    │  periodically runs    │
    │  health checks)       │
    └───────────┬───────────┘
                │
      ┌─────────▼───────────┐
      │ External APIs        │
      │ (FastAPI, Django...) │
      │ must expose /health  │
      └──────────────────────┘
css
Copy code

Each monitored API exposes a simple **`GET /health`** endpoint returning:
```json
{
  "status": "healthy",
  "service": "my-api"
}
🏗️ Tech Stack
Layer	Technology
Backend	Django, Django REST Framework
Scheduler	APScheduler (or Celery + Redis, optional)
Database	PostgreSQL (or SQLite for dev)
Containerization	Docker, Docker Compose
Language	Python 3.11+