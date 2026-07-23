import pytest

from apps.memory.models import TMEntry
from apps.memory.services import TranslationMemoryService


@pytest.mark.django_db
class TestTMEntryModel:
    def test_tm_entry_creation(self, tm_entry):
        assert tm_entry.pk is not None
        assert tm_entry.source_text == "Hello world"

    def test_tm_entry_str(self, tm_entry):
        s = str(tm_entry)
        assert "Hello world" in s
        assert "नमस्ते संसार" in s

    def test_tm_entry_quality_score(self, tm_entry):
        assert tm_entry.quality_score == 0.95

    def test_tm_entry_context(self, tm_entry):
        assert tm_entry.context == "Greeting"

    def test_tm_entry_ordering(self, user):
        e1 = TMEntry.objects.create(
            user=user, source_lang="en", target_lang="hi",
            source_text="First", target_text="पहला",
        )
        e2 = TMEntry.objects.create(
            user=user, source_lang="en", target_lang="hi",
            source_text="Second", target_text="दूसरा",
        )
        entries = list(TMEntry.objects.filter(user=user))
        assert entries[0].pk == e2.pk

    def test_tm_entry_index(self, user):
        e = TMEntry.objects.create(
            user=user, source_lang="en", target_lang="hi",
            source_text="Indexed", target_text="इंडेक्स्ड",
        )
        assert e.pk is not None

    def test_tm_entry_per_user_isolation(self, user, pro_user):
        TMEntry.objects.create(
            user=user, source_lang="en", target_lang="hi",
            source_text="User1", target_text="यूजर1",
        )
        TMEntry.objects.create(
            user=pro_user, source_lang="en", target_lang="hi",
            source_text="User2", target_text="यूजर2",
        )
        assert TMEntry.objects.filter(user=user).count() == 1
        assert TMEntry.objects.filter(user=pro_user).count() == 1


@pytest.mark.django_db
class TestTranslationMemoryService:
    def test_add_entry(self, user):
        entry = TranslationMemoryService.add_entry(
            user=user, source_lang="en", target_lang="hi",
            source_text="Test add", target_text="परीक्षा जोड़ना",
            context="Service test",
        )
        assert entry.pk is not None
        assert entry.quality_score == 1.0

    def test_fuzzy_match(self, user):
        TMEntry.objects.create(
            user=user, source_lang="en", target_lang="hi",
            source_text="Hello, how are you?", target_text="नमस्ते, आप कैसे हैं?",
        )
        result = TranslationMemoryService.find_matches(
            user, "en", "hi", "Hello, how are you today?"
        )
        assert len(result) > 0
        assert result[0]['score'] > 0.75

    def test_fuzzy_match_no_results(self, user):
        TMEntry.objects.create(
            user=user, source_lang="en", target_lang="hi",
            source_text="Hello", target_text="नमस्ते",
        )
        result = TranslationMemoryService.find_matches(
            user, "en", "hi", "xyz123 unrelated"
        )
        assert len(result) == 0

    def test_fuzzy_match_limit(self, user):
        for i in range(15):
            TMEntry.objects.create(
                user=user, source_lang="en", target_lang="hi",
                source_text=f"Hello {i}", target_text=f"नमस्ते {i}",
            )
        result = TranslationMemoryService.find_matches(
            user, "en", "hi", "Hello 0", limit=5
        )
        assert len(result) <= 5

    def test_fuzzy_match_user_isolation(self, user, pro_user):
        TMEntry.objects.create(
            user=user, source_lang="en", target_lang="hi",
            source_text="My entry", target_text="मेरा प्रविष्टि",
        )
        TMEntry.objects.create(
            user=pro_user, source_lang="en", target_lang="hi",
            source_text="My entry", target_text="उनका प्रविष्टि",
        )
        result = TranslationMemoryService.find_matches(
            user, "en", "hi", "My entry"
        )
        assert len(result) == 1
        assert result[0]['target'] == "मेरा प्रविष्टि"


@pytest.mark.django_db
class TestTMViews:
    def test_tm_list(self, authenticated_client):
        resp = authenticated_client.get("/tm/")
        assert resp.status_code == 200

    def test_tm_add_page(self, authenticated_client):
        resp = authenticated_client.get("/tm/add/")
        assert resp.status_code == 200

    def test_tm_add_entry(self, authenticated_client, user):
        resp = authenticated_client.post("/tm/add/", {
            "source_lang": "en",
            "target_lang": "hi",
            "source_text": "New source",
            "target_text": "नया स्रोत",
            "context": "View test",
        })
        assert resp.status_code == 302
        assert TMEntry.objects.filter(user=user, source_text="New source").exists()

    def test_tm_delete(self, authenticated_client, tm_entry):
        resp = authenticated_client.post(f"/tm/{tm_entry.pk}/delete/")
        assert resp.status_code == 302
        assert not TMEntry.objects.filter(pk=tm_entry.pk).exists()

    def test_tm_requires_login(self, client):
        resp = client.get("/tm/")
        assert resp.status_code == 302

    def test_tm_export(self, authenticated_client):
        resp = authenticated_client.get("/tm/export/en/hi/")
        assert resp.status_code == 200
        assert "xml" in resp["Content-Type"]

    def test_export_tmx_service(self, user):
        TMEntry.objects.create(
            user=user, source_lang="en", target_lang="hi",
            source_text="Hello", target_text="नमस्ते",
        )
        TMEntry.objects.create(
            user=user, source_lang="en", target_lang="hi",
            source_text="World", target_text="संसार",
        )
        tmx = TranslationMemoryService.export_tmx(user, "en", "hi")
        assert '<?xml version="1.0"' in tmx
        assert '<tmx version="1.4">' in tmx
        assert 'Hello' in tmx
        assert 'नमस्ते' in tmx
        assert 'World' in tmx
        assert 'संसार' in tmx
        assert 'xml:lang="en"' in tmx
        assert 'xml:lang="hi"' in tmx

    def test_export_tmx_escapes_xml(self, user):
        TMEntry.objects.create(
            user=user, source_lang="en", target_lang="hi",
            source_text="A <b>bold</b> &amp; text", target_text="टेक्स्ट",
        )
        tmx = TranslationMemoryService.export_tmx(user, "en", "hi")
        assert '&lt;b' in tmx
        assert '&amp;amp;' in tmx

    def test_export_tmx_empty(self, user):
        tmx = TranslationMemoryService.export_tmx(user, "en", "fr")
        assert '<body>' in tmx
        assert '</body>' in tmx
        assert '<tu>' not in tmx
