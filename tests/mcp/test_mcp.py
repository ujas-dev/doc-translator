import pytest
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.glossaries.models import Glossary, GlossaryEntry
from apps.memory.models import TMEntry


@pytest.mark.django_db
class TestMCPTranslate:
    @patch('apps.mcp.views.translate_text', return_value='नमस्ते दुनिया')
    def test_translate_text(self, mock_translate, authenticated_client):
        resp = authenticated_client.post(
            '/api/mcp/translate/',
            {'text': 'Hello world', 'source_lang': 'en', 'target_lang': 'hi'},
            content_type='application/json',
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['translated'] == 'नमस्ते दुनिया'
        assert data['source_lang'] == 'en'
        assert data['target_lang'] == 'hi'
        mock_translate.assert_called_once_with(
            'Hello world', source='en', target='hi', style='fluid',
        )

    def test_translate_text_invalid(self, authenticated_client):
        resp = authenticated_client.post(
            '/api/mcp/translate/',
            {},
            content_type='application/json',
        )
        assert resp.status_code == 400

    def test_translate_text_with_style(self, authenticated_client):
        with patch('apps.mcp.views.translate_text', return_value='Hello') as mock:
            resp = authenticated_client.post(
                '/api/mcp/translate/',
                {'text': 'Bonjour', 'source_lang': 'fr', 'target_lang': 'en', 'style': 'formal'},
                content_type='application/json',
            )
            assert resp.status_code == 200
            mock.assert_called_once_with(
                'Bonjour', source='fr', target='en', style='formal',
            )

    def test_translate_unauthenticated(self, client):
        resp = client.post(
            '/api/mcp/translate/',
            {'text': 'Hello', 'source_lang': 'en', 'target_lang': 'hi'},
            content_type='application/json',
        )
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestMCPTranslateDoc:
    def test_translate_document(self, authenticated_client):
        content = b"Test document content"
        file = SimpleUploadedFile("test.txt", content, content_type="text/plain")

        resp = authenticated_client.post(
            '/api/mcp/translate/document/',
            {'file': file, 'target_lang': 'hi'},
            format='multipart',
        )
        assert resp.status_code == 201
        data = resp.json()
        assert 'job_id' in data
        assert data['status'] == 'queued'

    def test_translate_document_invalid(self, authenticated_client):
        resp = authenticated_client.post(
            '/api/mcp/translate/document/',
            {},
            format='multipart',
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestMCPGlossary:
    def test_glossary_search(self, authenticated_client, user, glossary):
        resp = authenticated_client.get(
            f'/api/mcp/glossary/?glossary_id={glossary.pk}&text=hello',
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['glossary'] == 'Test Glossary'
        assert len(data['matches']) == 1
        assert data['matches'][0]['source'] == 'hello'
        assert data['matches'][0]['target'] == 'namaste'

    def test_glossary_not_found(self, authenticated_client):
        resp = authenticated_client.get(
            '/api/mcp/glossary/?glossary_id=99999&text=hello',
        )
        assert resp.status_code == 404

    def test_glossary_no_match(self, authenticated_client, glossary):
        resp = authenticated_client.get(
            f'/api/mcp/glossary/?glossary_id={glossary.pk}&text=zzzzz',
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data['matches']) == 0

    def test_glossary_unauthenticated(self, client):
        resp = client.get('/api/mcp/glossary/?glossary_id=1&text=hello')
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestMCPTMSearch:
    def test_tm_search(self, authenticated_client, user, tm_entry):
        resp = authenticated_client.post(
            '/api/mcp/tm/search/',
            {'source_text': 'Hello world', 'source_lang': 'en', 'target_lang': 'hi'},
            content_type='application/json',
        )
        assert resp.status_code == 200
        data = resp.json()
        assert 'matches' in data

    def test_tm_search_no_match(self, authenticated_client):
        resp = authenticated_client.post(
            '/api/mcp/tm/search/',
            {'source_text': 'xyzzy', 'source_lang': 'en', 'target_lang': 'hi'},
            content_type='application/json',
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data['matches']) == 0

    def test_tm_search_invalid(self, authenticated_client):
        resp = authenticated_client.post(
            '/api/mcp/tm/search/',
            {},
            content_type='application/json',
        )
        assert resp.status_code == 400
