import os
import fitz


FONT_DIR = os.environ.get('PDF_FONT_DIR', '/tmp')

FONT_MAP = {
    'hi': os.path.join(FONT_DIR, 'NotoSansDevanagari-Regular.ttf'),
    'gu': os.path.join(FONT_DIR, 'NotoSansGujarati-Regular.ttf'),
}


def _load_font(lang: str) -> fitz.Font:
    font_path = FONT_MAP.get(lang)
    if font_path and os.path.exists(font_path):
        return fitz.Font(fontfile=font_path)
    return fitz.Font("helv")


def create_bilingual_pdf(
    input_path: str,
    output_path: str,
    translate_fn,
    source_lang: str = 'en',
    target_lang: str = 'hi',
) -> dict:
    doc = fitz.open(input_path)
    src_font = _load_font(source_lang)
    tgt_font = _load_font(target_lang)
    stats = {"pages": 0, "segments": 0}

    out_doc = fitz.open()

    for page_num in range(len(doc)):
        src_page = doc[page_num]
        text_dict = src_page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        segments = []
        for block in text_dict["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text or len(text) < 3:
                        continue
                    bbox = fitz.Rect(span["bbox"])
                    font_size = span["size"]
                    translated = translate_fn(text, source_lang, target_lang)
                    if translated:
                        segments.append({
                            "bbox": bbox,
                            "source": text,
                            "translated": translated,
                            "font_size": font_size,
                        })
                        stats["segments"] += 1

        src_height = src_page.rect.height
        tgt_height = max(src_height, len(segments) * 30 + 100)
        page_height = src_height + tgt_height + 40

        new_page = out_doc.new_page(width=src_page.rect.width, height=page_height)

        new_page.draw_rect(fitz.Rect(0, 0, src_page.rect.width, src_height),
                          color=None, fill=(0.98, 0.98, 0.98))

        pix = src_page.get_pixmap()
        new_page.insert_image(fitz.Rect(0, 0, src_page.rect.width, src_height), pixmap=pix)

        separator_y = src_height + 10
        new_page.draw_line(fitz.Point(0, separator_y),
                          fitz.Point(src_page.rect.width, separator_y),
                          color=(0.2, 0.4, 0.8), width=1)

        tw_src = fitz.TextWriter(new_page.rect)
        tw_tgt = fitz.TextWriter(new_page.rect)

        y_offset = src_height + 30
        for seg in segments:
            try:
                tw_src.append(
                    fitz.Point(20, y_offset),
                    f"▶ {seg['source']}",
                    font=src_font,
                    fontsize=10,
                )
                tw_tgt.append(
                    fitz.Point(20, y_offset + 14),
                    f"  {seg['translated']}",
                    font=tgt_font,
                    fontsize=10,
                )
                y_offset += 32
            except Exception:
                pass

        try:
            tw_src.write_text(new_page)
            tw_tgt.write_text(new_page)
        except Exception:
            pass

        stats["pages"] += 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_doc.save(output_path)
    out_doc.close()
    doc.close()
    return stats
