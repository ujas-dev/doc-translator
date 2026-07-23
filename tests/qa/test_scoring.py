import pytest
from apps.qa.services import QAScoringService


class TestLengthConsistency:
    def test_normal_ratio(self):
        result = QAScoringService.score_length_consistency("Hello world", "Hola mundo")
        assert result['score'] == 1.0

    def test_short_translation(self):
        result = QAScoringService.score_length_consistency("Hello world", "Hi")
        assert result['score'] < 1.0

    def test_empty_source(self):
        result = QAScoringService.score_length_consistency("", "Hola")
        assert result['score'] == 1.0


class TestTermConsistency:
    def test_no_glossary(self):
        result = QAScoringService.score_term_consistency("Hello", "Hola", None)
        assert result['score'] == 1.0

    def test_with_glossary(self):
        glossary = {'hello': 'hola', 'world': 'mundo'}
        result = QAScoringService.score_term_consistency("hello world", "Hola mundo", glossary)
        assert result['score'] == 1.0


class TestEmptySegments:
    def test_no_empty(self):
        result = QAScoringService.score_empty_segments(["Hello", "World"])
        assert result['score'] == 1.0

    def test_some_empty(self):
        result = QAScoringService.score_empty_segments(["Hello", "", "World", ""])
        assert result['score'] == 0.5


class TestUntranslated:
    def test_different_text(self):
        result = QAScoringService.score_untranslated("Hello", "Hola")
        assert result['score'] == 1.0

    def test_same_text(self):
        result = QAScoringService.score_untranslated("Hello", "Hello")
        assert result['score'] <= 0.7


class TestRunAllChecks:
    def test_returns_all_scores(self):
        results = QAScoringService.run_all_checks("Hello", "Hola")
        assert 'length_consistency' in results
        assert 'term_consistency' in results
        assert 'untranslated' in results
        assert 'overall' in results

    def test_overall_score_range(self):
        results = QAScoringService.run_all_checks("Hello", "Hola")
        assert 0.0 <= results['overall']['score'] <= 1.0
