import pytest
from apps.translation.services import chunk_text, translate_document


class TestChunkText:
    def test_short_text_single_chunk(self):
        chunks = chunk_text("Hello world")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_empty_text(self):
        chunks = chunk_text("")
        assert len(chunks) == 0

    def test_paragraph_splitting(self):
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = chunk_text(text, max_len=20)
        assert len(chunks) >= 2

    def test_long_paragraph_word_split(self):
        text = " ".join(["word"] * 2000)
        chunks = chunk_text(text, max_len=4500)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) <= 4600

    def test_respects_paragraph_boundaries(self):
        text = "Short.\n\n" + "x " * 1000
        chunks = chunk_text(text, max_len=4500)
        assert len(chunks) >= 2
        assert chunks[0] == "Short."


@pytest.mark.django_db
class TestTranslateDocument:
    @pytest.mark.skipif(True, reason="Requires running translation backends")
    def test_translate_document_returns_text(self):
        result = translate_document("Hello world", source="en", target="hi")
        assert isinstance(result, str)
        assert len(result) > 0
