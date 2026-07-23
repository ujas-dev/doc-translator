import pytest
from unittest.mock import patch, MagicMock

from apps.status.models import ServiceStatus
from apps.status.services import (
    check_postgresql,
    check_redis,
    check_libretranslate,
    check_ollama,
    check_django_app,
    run_all_checks,
)


@pytest.mark.django_db
class TestStatusModels:
    def test_service_status_creation(self):
        ss = ServiceStatus.objects.create(
            service_name="postgresql", status="healthy", latency_ms=15
        )
        assert ss.pk is not None

    def test_service_status_str(self):
        ss = ServiceStatus.objects.create(service_name="redis", status="down")
        assert "redis" in str(ss)
        assert "down" in str(ss)

    def test_status_color_healthy(self):
        ss = ServiceStatus(service_name="test", status="healthy")
        assert ss.status_color == "green"

    def test_status_color_down(self):
        ss = ServiceStatus(service_name="test", status="down")
        assert ss.status_color == "red"

    def test_status_color_degraded(self):
        ss = ServiceStatus(service_name="test", status="degraded")
        assert ss.status_color == "yellow"

    def test_status_icon(self):
        ss = ServiceStatus(service_name="test", status="healthy")
        assert "check" in ss.status_icon

    def test_unique_service_name(self):
        ServiceStatus.objects.create(service_name="test", status="healthy")
        with pytest.raises(Exception):
            ServiceStatus.objects.create(service_name="test", status="down")


@pytest.mark.django_db
class TestHealthChecks:
    def test_check_django_app(self):
        result = check_django_app()
        assert result["status"] == "healthy"

    @patch("apps.status.services.connection")
    def test_check_postgresql_success(self, mock_conn):
        mock_conn.cursor.return_value.__enter__ = lambda s: s
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.execute = MagicMock()
        result = check_postgresql()
        assert result["status"] == "healthy"
        assert "latency_ms" in result

    @patch("apps.status.services.connection")
    def test_check_postgresql_failure(self, mock_conn):
        mock_conn.cursor.side_effect = Exception("Connection refused")
        result = check_postgresql()
        assert result["status"] == "down"
        assert "Connection refused" in result["error"]

    @patch("apps.status.services.redis")
    def test_check_redis_success(self, mock_redis):
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        mock_redis.from_url.return_value = mock_instance
        result = check_redis()
        assert result["status"] == "healthy"

    @patch("apps.status.services.redis")
    def test_check_redis_failure(self, mock_redis):
        mock_redis.from_url.side_effect = Exception("Connection refused")
        result = check_redis()
        assert result["status"] == "down"

    @patch("apps.status.services.requests.get")
    def test_check_libretranslate_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        result = check_libretranslate()
        assert result["status"] == "healthy"

    @patch("apps.status.services.requests.get")
    def test_check_libretranslate_down(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        result = check_libretranslate()
        assert result["status"] == "down"

    @patch("apps.status.services.requests.get")
    def test_check_ollama_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        result = check_ollama()
        assert result["status"] == "healthy"

    @patch("apps.status.services.requests.get")
    def test_check_ollama_down(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        result = check_ollama()
        assert result["status"] == "down"


@pytest.mark.django_db
class TestRunAllChecks:
    @patch("apps.status.services.check_postgresql", return_value={"status": "healthy", "latency_ms": 10})
    @patch("apps.status.services.check_redis", return_value={"status": "healthy", "latency_ms": 5})
    @patch("apps.status.services.check_libretranslate", return_value={"status": "healthy", "latency_ms": 100})
    @patch("apps.status.services.check_ollama", return_value={"status": "down", "latency_ms": 0, "error": "Connection refused"})
    @patch("apps.status.services.check_celery_worker", return_value={"status": "unknown", "latency_ms": 0})
    @patch("apps.status.services.check_celery_beat", return_value={"status": "unknown", "latency_ms": 0})
    @patch("apps.status.services.check_django_app", return_value={"status": "healthy", "latency_ms": 1})
    def test_overall_degraded_when_one_down(self, *mocks):
        result = run_all_checks()
        assert result["overall"] == "down"
        assert len(result["services"]) == 7

    @patch("apps.status.services.check_postgresql", return_value={"status": "healthy", "latency_ms": 10})
    @patch("apps.status.services.check_redis", return_value={"status": "healthy", "latency_ms": 5})
    @patch("apps.status.services.check_libretranslate", return_value={"status": "healthy", "latency_ms": 100})
    @patch("apps.status.services.check_ollama", return_value={"status": "healthy", "latency_ms": 200})
    @patch("apps.status.services.check_celery_worker", return_value={"status": "healthy", "latency_ms": 3})
    @patch("apps.status.services.check_celery_beat", return_value={"status": "healthy", "latency_ms": 2})
    @patch("apps.status.services.check_django_app", return_value={"status": "healthy", "latency_ms": 1})
    def test_overall_healthy(self, *mocks):
        result = run_all_checks()
        assert result["overall"] == "healthy"


@pytest.mark.django_db
class TestStatusViews:
    def test_public_status(self, client):
        resp = client.get("/status/")
        assert resp.status_code == 200

    def test_detail_status_requires_staff(self, authenticated_client):
        resp = authenticated_client.get("/status/detail/")
        assert resp.status_code == 302

    def test_detail_status_staff(self, admin_client):
        resp = admin_client.get("/status/detail/")
        assert resp.status_code == 200

    def test_check_service_endpoint(self, admin_client):
        resp = admin_client.get("/status/check/django_app/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_check_unknown_service(self, admin_client):
        resp = admin_client.get("/status/check/nonexistent/")
        assert resp.status_code == 404

    def test_check_all_services(self, admin_client):
        resp = admin_client.get("/status/check-all/")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall" in data
        assert "services" in data

    def test_check_service_stores_result(self, admin_client):
        admin_client.get("/status/check/django_app/")
        ss = ServiceStatus.objects.get(service_name="django_app")
        assert ss.status == "healthy"
