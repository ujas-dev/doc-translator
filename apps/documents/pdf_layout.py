import os
import re
import fitz


FONT_DIR = os.environ.get('PDF_FONT_DIR', '/tmp')

FONT_MAP = {
    'hi': os.path.join(FONT_DIR, 'NotoSansDevanagari-Regular.ttf'),
    'gu': os.path.join(FONT_DIR, 'NotoSansGujarati-Regular.ttf'),
}

FORMULA_PATTERNS = [
    re.compile(r'^[a-zA-Z0-9\s\+\-\*/\=\(\)\[\]\{\}\,\.\;\:]+$'),
    re.compile(r'[\+\-\*/\=\(\)\[\]\{\}]'),
    re.compile(r'^[A-Z][a-z]?\d*$'),
    re.compile(r'^\d+[\.\d]*$'),
]


def _is_formula(text: str) -> bool:
    """Detect if text looks like a mathematical formula."""
    text = text.strip()
    if not text:
        return False

    if len(text) < 2:
        return False

    formula_chars = set('+-*/=()[]{}^√∑∏∫∂√∞≈≠≤≥±×÷')
    if any(c in formula_chars for c in text):
        return True

    for pattern in FORMULA_PATTERNS:
        if pattern.match(text):
            return True

    if re.match(r'^[A-Z][a-z]?$', text) and len(text) <= 2:
        return True

    return False


def _load_font(target_lang: str) -> fitz.Font:
    font_path = FONT_MAP.get(target_lang)
    if font_path and os.path.exists(font_path):
        return fitz.Font(fontfile=font_path)
    return fitz.Font("helv")


def translate_pdf_preserve(
    input_path: str,
    output_path: str,
    translate_fn,
    source_lang: str = 'en',
    target_lang: str = 'hi',
) -> dict:
    doc = fitz.open(input_path)
    font = _load_font(target_lang)
    stats = {"pages": 0, "segments": 0, "characters": 0}

    for page_num in range(len(doc)):
        page = doc[page_num]
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        replacements = []

        for block in text_dict["blocks"]:
            if block["type"] != 0:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text or len(text) < 3:
                        continue

                    if _is_formula(text):
                        continue

                    bbox = fitz.Rect(span["bbox"])
                    font_size = span["size"]

                    translated = translate_fn(text, source_lang, target_lang)
                    if translated and translated != text:
                        replacements.append({
                            "bbox": bbox,
                            "original": text,
                            "translated": translated,
                            "font_size": font_size,
                        })
                        stats["segments"] += 1
                        stats["characters"] += len(text)

        for rep in replacements:
            page.draw_rect(rep["bbox"], color=None, fill=(1, 1, 1))
            tw = fitz.TextWriter(page.rect)
            try:
                tw.append(
                    fitz.Point(rep["bbox"].x0, rep["bbox"].y0 + rep["font_size"]),
                    rep["translated"],
                    font=font,
                    fontsize=rep["font_size"],
                )
                tw.write_text(page)
            except Exception:
                page.insert_text(
                    fitz.Point(rep["bbox"].x0, rep["bbox"].y0 + rep["font_size"]),
                    rep["translated"],
                    fontname="helv",
                    fontsize=rep["font_size"],
                )

        stats["pages"] += 1

    doc.save(output_path)
    doc.close()
    return stats
