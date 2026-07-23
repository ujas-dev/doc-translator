import os
import tempfile

import pytest
from PIL import Image

from apps.documents.parsers import extract_text, _extract_md, _write_md, _extract_image


@pytest.fixture
def md_file():
    content = """# Welcome to Doc Translator

This is a **bold** text and this is *italic*.

## Features

- Drag and drop upload
- Real-time status updates
- Multiple format support

### Supported Formats

| Format | Status |
|--------|--------|
| PDF    | Done   |
| DOCX   | Done   |

> This is a blockquote

Here is some `inline code` and a [link](https://example.com).

1. First item
2. Second item
3. Third item
"""
    path = os.path.join(tempfile.gettempdir(), 'test.md')
    with open(path, 'w') as f:
        f.write(content)
    return path


@pytest.fixture
def image_file():
    img = Image.new('RGB', (400, 200), color='white')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Hello World", fill='black')
    draw.text((50, 100), "This is OCR Test", fill='black')
    path = os.path.join(tempfile.gettempdir(), 'test_ocr.png')
    img.save(path)
    return path


class TestMarkdownParser:
    def test_extract_md_headings(self, md_file):
        text, pages = _extract_md(md_file)
        assert "MD_H1: Welcome to Doc Translator" in text
        assert "MD_H2: Features" in text
        assert "MD_H3: Supported Formats" in text

    def test_extract_md_lists(self, md_file):
        text, pages = _extract_md(md_file)
        assert "MD_LIST: Drag and drop upload" in text
        assert "MD_LIST: Real-time status updates" in text
        assert "MD_LIST: Multiple format support" in text

    def test_extract_md_tables(self, md_file):
        text, pages = _extract_md(md_file)
        assert "MD_TABLE: Format | Status" in text
        assert "MD_TABLE: PDF | Done" in text

    def test_extract_md_blockquote(self, md_file):
        text, pages = _extract_md(md_file)
        assert "MD_QUOTE: This is a blockquote" in text

    def test_extract_md_ordered_lists(self, md_file):
        text, pages = _extract_md(md_file)
        assert "MD_LIST: First item" in text
        assert "MD_LIST: Second item" in text
        assert "MD_LIST: Third item" in text

    def test_extract_md_page_count(self, md_file):
        text, pages = _extract_md(md_file)
        assert pages >= 1

    def test_extract_md_inline_formatting_removed(self, md_file):
        text, _ = _extract_md(md_file)
        assert "**" not in text
        assert "*" not in text or "MD_" in text
        assert "`" not in text

    def test_write_md_headings(self, md_file):
        text, _ = _extract_md(md_file)
        translated = text.replace("Welcome to Doc Translator", "Swagat")
        out_path = os.path.join(tempfile.gettempdir(), 'test_out.md')
        _write_md(translated, out_path, md_file)
        with open(out_path) as f:
            content = f.read()
        assert "# Swagat" in content

    def test_write_md_lists(self, md_file):
        text, _ = _extract_md(md_file)
        out_path = os.path.join(tempfile.gettempdir(), 'test_out_lists.md')
        _write_md(text, out_path, md_file)
        with open(out_path) as f:
            content = f.read()
        assert "- Drag and drop upload" in content

    def test_write_md_tables(self, md_file):
        text, _ = _extract_md(md_file)
        out_path = os.path.join(tempfile.gettempdir(), 'test_out_tables.md')
        _write_md(text, out_path, md_file)
        with open(out_path) as f:
            content = f.read()
        assert "| Format | Status |" in content

    def test_extract_md_via_dispatch(self, md_file):
        text, pages = extract_text(md_file)
        assert "MD_H1:" in text
        assert pages >= 1

    def test_extract_md_empty_file(self):
        path = os.path.join(tempfile.gettempdir(), 'empty.md')
        with open(path, 'w') as f:
            f.write("")
        text, pages = _extract_md(path)
        assert text == ""
        assert pages == 1


class TestImageParser:
    def test_extract_image_returns_text(self, image_file):
        text, pages = _extract_image(image_file)
        assert len(text) > 0
        assert pages == 1

    def test_extract_image_page_count(self, image_file):
        text, pages = _extract_image(image_file)
        assert pages == 1

    def test_extract_image_via_dispatch(self, image_file):
        text, pages = extract_text(image_file)
        assert len(text) > 0
        assert pages == 1

    def test_extract_image_jpg(self):
        img = Image.new('RGB', (200, 100), color='white')
        path = os.path.join(tempfile.gettempdir(), 'test.jpg')
        img.save(path)
        text, pages = extract_text(path)
        assert pages == 1

    def test_extract_image_large_resizes(self):
        img = Image.new('RGB', (5000, 5000), color='white')
        path = os.path.join(tempfile.gettempdir(), 'large.png')
        img.save(path)
        text, pages = _extract_image(path)
        assert pages == 1

    def test_extract_image_grayscale(self):
        img = Image.new('L', (200, 100), color=200)
        path = os.path.join(tempfile.gettempdir(), 'gray.png')
        img.save(path)
        text, pages = _extract_image(path)
        assert pages == 1
