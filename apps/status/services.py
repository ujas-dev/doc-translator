import time
import structlog

import redis
import requests
from django.conf import settings
from django.db import connection

logger = structlog.get_logger(__name__)

SERVICES = [
    {
        "name": "postgresql",
        "label": "PostgreSQL Database",
        "icon": "fa-database",
        "check_fn": "check_postgresql",
    },
    {
        "name": "redis",
        "label": "Redis Cache",
        "icon": "fa-bolt",
        "check_fn": "check_redis",
    },
    {
        "name": "libretranslate",
        "label": "LibreTranslate",
        "icon": "fa-language",
        "check_fn": "check_libretranslate",
    },
    {
        "name": "ollama",
        "label": "Ollama LLM",
        "icon": "fa-robot",
        "check_fn": "check_ollama",
    },
    {
        "name": "celery_worker",
        "label": "Celery Worker",
        "icon": "fa-cogs",
        "check_fn": "check_celery_worker",
    },
    {
        "name": "celery_beat",
        "label": "Celery Beat",
        "icon": "fa-clock",
        "check_fn": "check_celery_beat",
    },
    {
        "name": "django_app",
        "label": "Django Application",
        "icon": "fa-server",
        "check_fn": "check_django_app",
    },
]


def check_postgresql():
    start = time.monotonic()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "healthy", "latency_ms": latency}
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "down", "latency_ms": latency, "error": str(e)}


def check_redis():
    start = time.monotonic()
    try:
        url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(url, socket_timeout=3)
        r.ping()
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "healthy", "latency_ms": latency}
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "down", "latency_ms": latency, "error": str(e)}


def check_libretranslate():
    start = time.monotonic()
    url = getattr(settings, 'LIBRETRANSLATE_URL', 'http://localhost:5000')
    try:
        resp = requests.get(f"{url}/languages", timeout=10)
        latency = int((time.monotonic() - start) * 1000)
        if resp.status_code == 200:
            return {"status": "healthy", "latency_ms": latency}
        return {"status": "degraded", "latency_ms": latency, "error": f"HTTP {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "down", "latency_ms": latency, "error": "Connection refused"}
    except requests.exceptions.Timeout:
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "down", "latency_ms": latency, "error": "Timeout after 10s"}
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "down", "latency_ms": latency, "error": str(e)}


def check_ollama():
    start = time.monotonic()
    url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
    try:
        resp = requests.get(f"{url}/api/tags", timeout=10)
        latency = int((time.monotonic() - start) * 1000)
        if resp.status_code == 200:
            return {"status": "healthy", "latency_ms": latency}
        return {"status": "degraded", "latency_ms": latency, "error": f"HTTP {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "down", "latency_ms": latency, "error": "Connection refused"}
    except requests.exceptions.Timeout:
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "down", "latency_ms": latency, "error": "Timeout after 10s"}
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "down", "latency_ms": latency, "error": str(e)}


def check_celery_worker():
    start = time.monotonic()
    try:
        url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/1')
        r = redis.from_url(url, socket_timeout=3)
        queue_len = r.llen('celery')
        latency = int((time.monotonic() - start) * 1000)

        from django.core.cache import cache
        last_heartbeat = cache.get('celery_worker_heartbeat')
        if last_heartbeat:
            age = time.time() - last_heartbeat
            if age < 120:
                return {"status": "healthy", "latency_ms": latency, "detail": f"Queue: {queue_len} tasks"}
            return {"status": "degraded", "latency_ms": latency, "error": f"Heartbeat stale ({int(age)}s ago)"}

        return {"status": "unknown", "latency_ms": latency, "detail": "No heartbeat recorded yet"}
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "down", "latency_ms": latency, "error": str(e)}


def check_celery_beat():
    start = time.monotonic()
    try:
        from django.core.cache import cache
        last_tick = cache.get('celery_beat_last_tick')
        latency = int((time.monotonic() - start) * 1000)

        if last_tick:
            age = time.time() - last_tick
            if age < 120:
                return {"status": "healthy", "latency_ms": latency}
            return {"status": "degraded", "latency_ms": latency, "error": f"Last tick {int(age)}s ago"}

        return {"status": "unknown", "latency_ms": latency, "detail": "No beat tick recorded yet"}
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        return {"status": "unknown", "latency_ms": latency, "error": str(e)}


def check_django_app():
    return {"status": "healthy", "latency_ms": 1}


def run_all_checks():
    results = []
    check_map = {s["check_fn"]: s for s in SERVICES}

    for svc in SERVICES:
        fn = globals()[svc["check_fn"]]
        try:
            result = fn()
        except Exception as e:
            result = {"status": "down", "latency_ms": 0, "error": str(e)}

        results.append({
            "name": svc["name"],
            "label": svc["label"],
            "icon": svc["icon"],
            **result,
        })

    overall = "healthy"
    for r in results:
        if r["status"] == "down":
            overall = "down"
            break
        if r["status"] == "degraded":
            overall = "degraded"

    return {"overall": overall, "services": results}
