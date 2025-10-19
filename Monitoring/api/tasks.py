from celery import shared_task
import asyncio
from .checks import run_due_checks

@shared_task(name="api.run_due_checks")
def run_due_checks_task():
    return run_due_checks()
