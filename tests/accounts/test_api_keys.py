import pytest
from django.contrib.auth.models import User

from apps.accounts.models import APIKey, UserProfile


@pytest.mark.django_db
class TestUserProfile:
    def test_profile_creation(self, user):
        assert user.profile.plan == "free"
        assert user.profile.documents_used_this_month == 0

    def test_can_translate_free_under_limit(self, user):
        user.profile.documents_used_this_month = 3
        user.profile.save()
        assert user.profile.can_translate is True

    def test_can_translate_free_at_limit(self, user):
        user.profile.documents_used_this_month = 5
        user.profile.save()
        assert user.profile.can_translate is False

    def test_can_translate_pro_unlimited(self, pro_user):
        pro_user.profile.documents_used_this_month = 100
        pro_user.profile.save()
        assert pro_user.profile.can_translate is True

    def test_can_translate_team_unlimited(self, team_user):
        team_user.profile.documents_used_this_month = 100
        team_user.profile.save()
        assert team_user.profile.can_translate is True

    def test_can_translate_enterprise_unlimited(self, enterprise_user):
        enterprise_user.profile.documents_used_this_month = 1000
        enterprise_user.profile.save()
        assert enterprise_user.profile.can_translate is True

    def test_max_pages_free(self, user):
        assert user.profile.max_pages_per_document == 10

    def test_max_pages_pro(self, pro_user):
        assert pro_user.profile.max_pages_per_document == 50

    def test_max_pages_team(self, team_user):
        assert team_user.profile.max_pages_per_document == 100

    def test_max_pages_enterprise(self, enterprise_user):
        assert enterprise_user.profile.max_pages_per_document == 9999

    def test_profile_str(self, user):
        assert str(user.profile) == "testuser (free)"

    def test_profile_str_pro(self, pro_user):
        assert str(pro_user.profile) == "testpro (pro)"


@pytest.mark.django_db
class TestAPIKeyModel:
    def test_api_key_creation(self, api_key):
        assert api_key.pk is not None
        assert len(api_key.key) == 64

    def test_api_key_auto_generates(self, user):
        key = APIKey.objects.create(user=user, name="Auto Gen")
        assert len(key.key) == 64

    def test_api_key_str(self, api_key):
        s = str(api_key)
        assert "Test Key" in s
        assert "..." in s

    def test_api_key_masked(self, api_key):
        masked = api_key.masked_key
        assert len(masked) == 15
        assert masked[8:11] == "..."

    def test_api_key_default_active(self, user):
        key = APIKey.objects.create(user=user, name="Default")
        assert key.is_active is True

    def test_api_key_default_rate_limit(self, user):
        key = APIKey.objects.create(user=user, name="Default")
        assert key.rate_limit == 100

    def test_api_key_unique(self, user):
        key1 = APIKey.objects.create(user=user, name="Key1")
        key2 = APIKey.objects.create(user=user, name="Key2")
        assert key1.key != key2.key

    def test_api_key_last_used_null(self, api_key):
        assert api_key.last_used_at is None
