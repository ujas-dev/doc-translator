import json

import pytest
from django.contrib.auth.models import User

from apps.glossaries.models import Glossary, GlossaryEntry
from apps.glossaries.services import GlossaryService


@pytest.mark.django_db
class TestGlossarySuggestService:
    def test_suggest_terms_exact_match(self, glossary):
        text = "Hello world, this is a test."
        suggestions = GlossaryService.suggest_terms(text, glossary)
        assert len(suggestions) == 2
        sources = [s['source'] for s in suggestions]
        assert 'hello' in sources
        assert 'world' in sources

    def test_suggest_terms_frequency(self, glossary):
        text = "hello hello hello world"
        suggestions = GlossaryService.suggest_terms(text, glossary)
        hello_match = next(s for s in suggestions if s['source'] == 'hello')
        world_match = next(s for s in suggestions if s['source'] == 'world')
        assert hello_match['frequency'] == 3
        assert world_match['frequency'] == 1

    def test_suggest_terms_sorted_by_frequency(self, glossary):
        text = "world world world hello"
        suggestions = GlossaryService.suggest_terms(text, glossary)
        assert suggestions[0]['source'] == 'world'
        assert suggestions[1]['source'] == 'hello'

    def test_suggest_terms_no_match(self, glossary):
        text = "xyz xyz xyz"
        suggestions = GlossaryService.suggest_terms(text, glossary)
        assert len(suggestions) == 0

    def test_suggest_terms_case_insensitive(self, glossary):
        text = "HELLO World"
        suggestions = GlossaryService.suggest_terms(text, glossary)
        assert len(suggestions) == 2

    def test_suggest_terms_empty_text(self, glossary):
        suggestions = GlossaryService.suggest_terms("", glossary)
        assert len(suggestions) == 0

    def test_suggest_terms_returns_metadata(self, glossary):
        text = "hello"
        suggestions = GlossaryService.suggest_terms(text, glossary)
        assert len(suggestions) == 1
        s = suggestions[0]
        assert 'source' in s
        assert 'target' in s
        assert 'context' in s
        assert 'is_preferred' in s
        assert 'match_type' in s
        assert 'frequency' in s
        assert s['match_type'] == 'exact'

    def test_suggest_terms_with_preferred(self, glossary):
        GlossaryEntry.objects.create(
            glossary=glossary, source="test", target="परीक्षा", is_preferred=True
        )
        text = "test"
        suggestions = GlossaryService.suggest_terms(text, glossary)
        assert len(suggestions) == 1
        assert suggestions[0]['is_preferred'] is True


@pytest.mark.django_db
class TestGlossarySuggestView:
    def test_suggest_requires_post(self, authenticated_client, glossary):
        resp = authenticated_client.get("/glossaries/suggest/")
        assert resp.status_code == 400

    def test_suggest_requires_login(self, client, glossary):
        resp = client.post("/glossaries/suggest/", {
            "text": "hello",
            "glossary_id": glossary.pk,
        })
        assert resp.status_code == 302

    def test_suggest_returns_suggestions(self, authenticated_client, glossary):
        resp = authenticated_client.post("/glossaries/suggest/", {
            "text": "hello world test",
            "glossary_id": glossary.pk,
        })
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert 'suggestions' in data
        assert 'total_matches' in data
        assert 'coverage_percentage' in data
        assert data['total_matches'] == 2

    def test_suggest_missing_params(self, authenticated_client, glossary):
        resp = authenticated_client.post("/glossaries/suggest/", {
            "text": "hello",
        })
        assert resp.status_code == 400

    def test_suggest_nonexistent_glossary(self, authenticated_client):
        resp = authenticated_client.post("/glossaries/suggest/", {
            "text": "hello",
            "glossary_id": 99999,
        })
        assert resp.status_code == 404

    def test_suggest_other_users_glossary(self, client, user):
        other_user = User.objects.create_user(username="other", password="pass123")
        other_glossary = Glossary.objects.create(
            user=other_user, name="Other Glossary", source_lang="en", target_lang="hi"
        )
        GlossaryEntry.objects.create(glossary=other_glossary, source="secret", target="गुप्त")
        client.login(username="testuser", password="testpass123")
        resp = client.post("/glossaries/suggest/", {
            "text": "secret",
            "glossary_id": other_glossary.pk,
        })
        assert resp.status_code == 404

    def test_suggest_empty_text(self, authenticated_client, glossary):
        resp = authenticated_client.post("/glossaries/suggest/", {
            "text": "",
            "glossary_id": glossary.pk,
        })
        assert resp.status_code == 400

    def test_suggest_coverage_percentage(self, authenticated_client, glossary):
        resp = authenticated_client.post("/glossaries/suggest/", {
            "text": "hello world",
            "glossary_id": glossary.pk,
        })
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data['coverage_percentage'] > 0
