import pytest
from difflib import SequenceMatcher


def _get_word_diff(source, translated):
    source_words = source.split()
    translated_words = translated.split()
    matcher = SequenceMatcher(None, source_words, translated_words)
    diff = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == 'equal':
            diff.append(('equal', source_words[i1:i2]))
        elif op == 'replace':
            diff.append(('changed', translated_words[j1:j2]))
        elif op == 'insert':
            diff.append(('inserted', translated_words[j1:j2]))
        elif op == 'delete':
            diff.append(('deleted', source_words[i1:i2]))
    return diff


class TestGetWordDiff:
    def test_identical_text(self):
        diff = _get_word_diff("Hello world", "Hello world")
        assert len(diff) == 1
        assert diff[0][0] == 'equal'

    def test_replaced_word(self):
        diff = _get_word_diff("Hello world", "Hola world")
        assert len(diff) == 2
        assert diff[0][0] == 'changed'
        assert diff[0][1] == ['Hola']
        assert diff[1][0] == 'equal'

    def test_inserted_word(self):
        diff = _get_word_diff("Hello", "Hello beautiful world")
        assert len(diff) == 2
        assert diff[0][0] == 'equal'
        assert diff[1][0] == 'inserted'
        assert 'beautiful' in diff[1][1]

    def test_deleted_word(self):
        diff = _get_word_diff("Hello beautiful world", "Hello world")
        assert len(diff) == 3
        ops = [d[0] for d in diff]
        assert 'deleted' in ops
        assert 'equal' in ops
        deleted = [d for d in diff if d[0] == 'deleted']
        assert 'beautiful' in deleted[0][1]

    def test_completely_different(self):
        diff = _get_word_diff("cat dog", "fish bird")
        assert len(diff) >= 1
        ops = [d[0] for d in diff]
        assert 'equal' not in ops

    def test_empty_source(self):
        diff = _get_word_diff("", "Hello")
        assert len(diff) == 1
        assert diff[0][0] == 'inserted'

    def test_empty_translation(self):
        diff = _get_word_diff("Hello", "")
        assert len(diff) == 1
        assert diff[0][0] == 'deleted'
