import pytest
from apps.memory.models import TMEntry


@pytest.mark.django_db
class TestTMLeverageView:
    def test_leverage_with_text(self, authenticated_client, user):
        TMEntry.objects.create(
            user=user,
            source_lang='en',
            target_lang='hi',
            source_text='Hello world',
            target_text='नमस्ते संसार',
        )
        resp = authenticated_client.get('/tm/leverage/?text=Hello+world&source_lang=en&target_lang=hi')
        assert resp.status_code == 200
        data = resp.json()
        assert 'leverage_percentage' in data
        assert 'total_segments' in data
        assert 'matches' in data

    def test_leverage_missing_text(self, authenticated_client):
        resp = authenticated_client.get('/tm/leverage/')
        assert resp.status_code == 400
        data = resp.json()
        assert 'error' in data

    def test_leverage_requires_login(self, client):
        resp = client.get('/tm/leverage/?text=hello')
        assert resp.status_code == 302

    def test_leverage_no_matches(self, authenticated_client, user):
        resp = authenticated_client.get('/tm/leverage/?text=xyz123&source_lang=en&target_lang=hi')
        assert resp.status_code == 200
        data = resp.json()
        assert data['leverage_percentage'] == 0
        assert data['total_segments'] == 0


@pytest.mark.django_db
class TestLeverageReport:
    def test_report_returns_count(self, user):
        from apps.memory.services import TranslationMemoryService
        TMEntry.objects.create(
            user=user, source_lang='en', target_lang='hi',
            source_text='Hello', target_text='नमस्ते',
        )
        TMEntry.objects.create(
            user=user, source_lang='en', target_lang='hi',
            source_text='Goodbye', target_text='अलविदा',
        )
        report = TranslationMemoryService.leverage_report(user, 'en', 'hi')
        assert report['total_entries'] == 2
        assert report['languages'] == 'en → hi'

    def test_report_empty(self, user):
        from apps.memory.services import TranslationMemoryService
        report = TranslationMemoryService.leverage_report(user, 'en', 'fr')
        assert report['total_entries'] == 0
        assert report['languages'] == 'en → fr'

    def test_report_user_isolation(self, user, pro_user):
        from apps.memory.services import TranslationMemoryService
        TMEntry.objects.create(
            user=user, source_lang='en', target_lang='hi',
            source_text='Mine', target_text='मेरा',
        )
        TMEntry.objects.create(
            user=pro_user, source_lang='en', target_lang='hi',
            source_text='Theirs', target_text='उनका',
        )
        report = TranslationMemoryService.leverage_report(user, 'en', 'hi')
        assert report['total_entries'] == 1
