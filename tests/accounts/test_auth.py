import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.accounts.models import APIKey, UserProfile


@pytest.mark.django_db
class TestRegistration:
    def test_register_page_loads(self, client):
        resp = client.get("/register/")
        assert resp.status_code == 200

    def test_register_creates_user(self, client):
        resp = client.post("/register/", {
            "username": "newuser",
            "email": "new@test.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        assert resp.status_code in (200, 302)
        assert User.objects.filter(username="newuser").exists()

    def test_register_creates_profile(self, client):
        client.post("/register/", {
            "username": "profileuser",
            "email": "prof@test.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        user = User.objects.get(username="profileuser")
        assert hasattr(user, 'profile')
        assert user.profile.plan == "free"

    def test_register_redirects_authenticated(self, authenticated_client):
        resp = authenticated_client.get("/register/")
        assert resp.status_code == 302

    def test_register_mismatched_passwords(self, client):
        resp = client.post("/register/", {
            "username": "baduser",
            "email": "bad@test.com",
            "password1": "StrongPass123!",
            "password2": "DifferentPass456!",
        })
        assert resp.status_code == 200
        assert not User.objects.filter(username="baduser").exists()


@pytest.mark.django_db
class TestLogin:
    def test_login_page_loads(self, client):
        resp = client.get("/login/")
        assert resp.status_code == 200

    def test_login_success(self, client, user):
        resp = client.post("/login/", {"username": "testuser", "password": "testpass123"})
        assert resp.status_code == 302
        assert resp.url == "/dashboard/"

    def test_login_failure(self, client, user):
        resp = client.post("/login/", {"username": "testuser", "password": "wrongpass"})
        assert resp.status_code == 200

    def test_login_redirects_authenticated(self, authenticated_client):
        resp = authenticated_client.get("/login/")
        assert resp.status_code == 302

    def test_login_sets_session(self, client, user):
        client.post("/login/", {"username": "testuser", "password": "testpass123"})
        assert "_auth_user_id" in client.session


@pytest.mark.django_db
class TestLogout:
    def test_logout(self, authenticated_client):
        resp = authenticated_client.post("/logout/")
        assert resp.status_code == 302

    def test_logout_clears_session(self, authenticated_client):
        authenticated_client.post("/logout/")
        assert "_auth_user_id" not in authenticated_client.session


@pytest.mark.django_db
class TestProfile:
    def test_profile_page_loads(self, authenticated_client):
        resp = authenticated_client.get("/profile/")
        assert resp.status_code == 200

    def test_profile_requires_login(self, client):
        resp = client.get("/profile/")
        assert resp.status_code == 302
        assert "login" in resp.url

    def test_profile_shows_plan(self, authenticated_client, user):
        resp = authenticated_client.get("/profile/")
        assert b"free" in resp.content.lower()


@pytest.mark.django_db
class TestAPIKeys:
    def test_api_keys_page_loads(self, authenticated_client):
        resp = authenticated_client.get("/api-keys/")
        assert resp.status_code == 200

    def test_create_api_key(self, authenticated_client, user):
        resp = authenticated_client.post("/api-keys/", {"name": "My Test Key"})
        assert resp.status_code == 302
        assert APIKey.objects.filter(user=user, name="My Test Key").exists()

    def test_create_api_key_generates_key(self, authenticated_client, user):
        authenticated_client.post("/api-keys/", {"name": "Generated Key"})
        key = APIKey.objects.get(user=user, name="Generated Key")
        assert len(key.key) == 64
        assert key.is_active is True

    def test_delete_api_key(self, authenticated_client, api_key):
        resp = authenticated_client.post(f"/api-keys/{api_key.pk}/delete/")
        assert resp.status_code == 302
        assert not APIKey.objects.filter(pk=api_key.pk).exists()

    def test_masked_key(self, api_key):
        masked = api_key.masked_key
        assert "..." in masked
        assert len(masked) == 15

    def test_api_keys_requires_login(self, client):
        resp = client.get("/api-keys/")
        assert resp.status_code == 302
