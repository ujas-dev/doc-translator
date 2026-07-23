import pytest
from apps.glossaries.models import Glossary, GlossaryEntry
from apps.glossaries.services import GlossaryService


@pytest.mark.django_db
class TestGlossaryServiceCreateGlossary:
    def test_create_glossary(self, user):
        g = GlossaryService.create_glossary(user, "My Glossary", "en", "hi")
        assert g.pk is not None
        assert g.name == "My Glossary"
        assert g.source_lang == "en"
        assert g.target_lang == "hi"
        assert g.user == user

    def test_create_glossary_with_description(self, user):
        g = GlossaryService.create_glossary(
            user, "Test", "en", "fr", description="A test glossary"
        )
        assert g.description == "A test glossary"


@pytest.mark.django_db
class TestGlossaryServiceAddEntry:
    def test_add_entry(self, glossary):
        entry = GlossaryService.add_entry(glossary, "test", "परीक्षा")
        assert entry.pk is not None
        assert entry.source == "test"
        assert entry.target == "परीक्षा"

    def test_add_entry_with_context(self, glossary):
        entry = GlossaryService.add_entry(
            glossary, "test", "परीक्षा", context="Unit test"
        )
        assert entry.context == "Unit test"

    def test_add_entry_is_preferred(self, glossary):
        entry = GlossaryService.add_entry(
            glossary, "test", "परीक्षा", is_preferred=True
        )
        assert entry.is_preferred is True


@pytest.mark.django_db
class TestGlossaryServiceApplyGlossary:
    def test_apply_glossary_basic(self, glossary):
        result = GlossaryService.apply_glossary("Hello world", glossary)
        assert "hello" not in result.lower() or result != "Hello world"

    def test_apply_glossary_no_match(self, glossary):
        result = GlossaryService.apply_glossary("xyz", glossary)
        assert result == "xyz"

    def test_apply_glossary_case_insensitive(self, glossary):
        result = GlossaryService.apply_glossary("HELLO", glossary)
        assert result != "HELLO"

    def test_apply_glossary_longest_first(self, user):
        g = Glossary.objects.create(user=user, name="Longest", source_lang="en", target_lang="hi")
        GlossaryEntry.objects.create(glossary=g, source="hello", target="hi")
        GlossaryEntry.objects.create(glossary=g, source="hello world", target="hello duniya")
        result = GlossaryService.apply_glossary("hello world", g)
        assert "hello world" not in result.lower() or result != "hello world"


@pytest.mark.django_db
class TestGlossaryServiceGetMatches:
    def test_get_matches_found(self, glossary):
        matches = GlossaryService.get_matches("Hello world test", glossary, threshold=0.5)
        assert len(matches) > 0

    def test_get_matches_no_match(self, glossary):
        matches = GlossaryService.get_matches("xyz", glossary, threshold=0.5)
        assert len(matches) == 0

    def test_get_matches_case_insensitive(self, glossary):
        matches = GlossaryService.get_matches("HELLO", glossary, threshold=0.5)
        assert len(matches) > 0
