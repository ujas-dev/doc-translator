import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.glossaries.models import Glossary, GlossaryEntry
from apps.glossaries.services import GlossaryService


@pytest.mark.django_db
class TestGlossaryModel:
    def test_glossary_creation(self, glossary):
        assert glossary.pk is not None
        assert glossary.name == "Test Glossary"

    def test_glossary_str(self, glossary):
        s = str(glossary)
        assert "Test Glossary" in s
        assert "en" in s
        assert "hi" in s

    def test_glossary_entry_count(self, glossary):
        assert glossary.entry_count == 2

    def test_glossary_unique_together(self, user):
        Glossary.objects.create(user=user, name="Unique", source_lang="en", target_lang="hi")
        with pytest.raises(Exception):
            Glossary.objects.create(user=user, name="Unique", source_lang="en", target_lang="gu")

    def test_glossary_ordering(self, user):
        g1 = Glossary.objects.create(user=user, name="First", source_lang="en", target_lang="hi")
        g2 = Glossary.objects.create(user=user, name="Second", source_lang="en", target_lang="gu")
        glossaries = list(Glossary.objects.filter(user=user))
        assert glossaries[0].pk == g2.pk

    def test_glossary_description(self, user):
        g = Glossary.objects.create(
            user=user, name="Desc", source_lang="en", target_lang="hi",
            description="A test glossary"
        )
        assert g.description == "A test glossary"


@pytest.mark.django_db
class TestGlossaryEntryModel:
    def test_entry_creation(self, glossary):
        entry = GlossaryEntry.objects.create(
            glossary=glossary, source="test", target="परीक्षा"
        )
        assert entry.pk is not None

    def test_entry_str(self, glossary):
        entry = glossary.entries.first()
        assert "hello" in str(entry)
        assert "namaste" in str(entry)

    def test_entry_unique_per_glossary(self, glossary):
        with pytest.raises(Exception):
            GlossaryEntry.objects.create(glossary=glossary, source="hello", target="dup")

    def test_entry_ordering(self, glossary):
        entries = list(glossary.entries.all())
        assert entries[0].source < entries[1].source

    def test_entry_context(self, glossary):
        entry = GlossaryEntry.objects.create(
            glossary=glossary, source="ctx", target="सीटीएक्स",
            context="Formal greeting"
        )
        assert entry.context == "Formal greeting"

    def test_entry_is_preferred(self, glossary):
        entry = GlossaryEntry.objects.create(
            glossary=glossary, source="pref", target="प्रेफ", is_preferred=True
        )
        assert entry.is_preferred is True


@pytest.mark.django_db
class TestGlossaryService:
    def test_import_csv(self, glossary, sample_csv_glossary):
        content = sample_csv_glossary.read().decode("utf-8")
        result = GlossaryService.import_csv(glossary, content)
        assert result["created"] >= 1

    def test_export_csv(self, glossary):
        csv_content = GlossaryService.export_csv(glossary)
        assert "source" in csv_content
        assert "target" in csv_content
        assert "hello" in csv_content


@pytest.mark.django_db
class TestGlossaryViews:
    def test_glossary_list(self, authenticated_client):
        resp = authenticated_client.get("/glossaries/")
        assert resp.status_code == 200

    def test_glossary_create_page(self, authenticated_client):
        resp = authenticated_client.get("/glossaries/create/")
        assert resp.status_code == 200

    def test_glossary_detail(self, authenticated_client, glossary):
        resp = authenticated_client.get(f"/glossaries/{glossary.pk}/")
        assert resp.status_code == 200

    def test_glossary_delete(self, authenticated_client, glossary):
        resp = authenticated_client.post(f"/glossaries/{glossary.pk}/delete/")
        assert resp.status_code == 302
        assert not Glossary.objects.filter(pk=glossary.pk).exists()

    def test_glossary_export(self, authenticated_client, glossary):
        resp = authenticated_client.get(f"/glossaries/{glossary.pk}/export/")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"

    def test_glossary_requires_login(self, client):
        resp = client.get("/glossaries/")
        assert resp.status_code == 302

    def test_add_entry(self, authenticated_client, glossary):
        resp = authenticated_client.post(f"/glossaries/{glossary.pk}/", {
            "add_entry": "",
            "source": "newterm",
            "target": "नयाटर्म",
        })
        assert resp.status_code == 302
        assert GlossaryEntry.objects.filter(glossary=glossary, source="newterm").exists()

    def test_delete_entry(self, authenticated_client, glossary):
        entry = glossary.entries.first()
        resp = authenticated_client.post(
            f"/glossaries/{glossary.pk}/entry/{entry.pk}/delete/"
        )
        assert resp.status_code == 302
        assert not GlossaryEntry.objects.filter(pk=entry.pk).exists()
