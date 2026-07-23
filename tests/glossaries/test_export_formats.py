import pytest
from apps.glossaries.models import Glossary, GlossaryEntry
from apps.glossaries.export import export_tbx, export_xliff
from apps.glossaries.services import GlossaryService


@pytest.mark.django_db
class TestGlossaryExportTBX:
    def test_tbx_export(self, glossary):
        content = export_tbx(glossary)
        assert 'tbx' in content.lower()
        assert 'hello' in content.lower()
        assert 'namaste' in content.lower()

    def test_tbx_export_with_context(self, glossary):
        GlossaryEntry.objects.create(
            glossary=glossary,
            source='test',
            target='परीक्षा',
            context='Unit testing',
        )
        content = export_tbx(glossary)
        assert 'Unit testing' in content

    def test_tbx_export_empty_glossary(self, user):
        g = Glossary.objects.create(user=user, name="Empty", source_lang='en', target_lang='hi')
        content = export_tbx(g)
        assert 'tbx' in content.lower()


@pytest.mark.django_db
class TestGlossaryExportXLIFF:
    def test_xliff_export(self, glossary):
        content = export_xliff(glossary)
        assert 'xliff' in content.lower()
        assert 'hello' in content.lower()
        assert 'namaste' in content.lower()

    def test_xliff_export_with_context(self, glossary):
        GlossaryEntry.objects.create(
            glossary=glossary,
            source='test',
            target='परीक्षा',
            context='Unit testing',
        )
        content = export_xliff(glossary)
        assert 'Unit testing' in content

    def test_xliff_export_empty_glossary(self, user):
        g = Glossary.objects.create(user=user, name="Empty", source_lang='en', target_lang='hi')
        content = export_xliff(g)
        assert 'xliff' in content.lower()


@pytest.mark.django_db
class TestGlossaryExportViewFormats:
    def test_export_tbx_via_view(self, authenticated_client, glossary):
        resp = authenticated_client.get(f'/glossaries/{glossary.pk}/export/?format=tbx')
        assert resp.status_code == 200
        assert 'xml' in resp['Content-Type']

    def test_export_xliff_via_view(self, authenticated_client, glossary):
        resp = authenticated_client.get(f'/glossaries/{glossary.pk}/export/?format=xliff')
        assert resp.status_code == 200
        assert 'xml' in resp['Content-Type']

    def test_export_csv_via_view(self, authenticated_client, glossary):
        resp = authenticated_client.get(f'/glossaries/{glossary.pk}/export/?format=csv')
        assert resp.status_code == 200
        assert 'text/csv' in resp['Content-Type']

    def test_export_requires_login(self, client, glossary):
        resp = client.get(f'/glossaries/{glossary.pk}/export/')
        assert resp.status_code == 302
