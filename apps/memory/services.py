from difflib import SequenceMatcher
from .models import TMEntry


class TranslationMemoryService:
    @staticmethod
    def add_entry(user, source_lang, target_lang, source_text, target_text, context='', quality=1.0):
        return TMEntry.objects.create(
            user=user,
            source_lang=source_lang,
            target_lang=target_lang,
            source_text=source_text,
            target_text=target_text,
            context=context,
            quality_score=quality,
        )

    @staticmethod
    def find_matches(user, source_lang, target_lang, text, threshold=0.75, limit=10):
        entries = TMEntry.objects.filter(
            user=user,
            source_lang=source_lang,
            target_lang=target_lang,
        )

        matches = []
        for entry in entries:
            ratio = SequenceMatcher(None, text.lower(), entry.source_text.lower()).ratio()
            if ratio >= threshold:
                matches.append({
                    "source": entry.source_text,
                    "target": entry.target_text,
                    "score": ratio,
                    "context": entry.context,
                    "quality": entry.quality_score,
                    "id": entry.pk,
                })

        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    @staticmethod
    def leverage_report(user, source_lang, target_lang):
        entries = TMEntry.objects.filter(
            user=user,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        return {
            "total_entries": entries.count(),
            "languages": f"{source_lang} → {target_lang}",
        }

    @staticmethod
    def export_tmx(user, source_lang, target_lang) -> str:
        entries = TMEntry.objects.filter(
            user=user,
            source_lang=source_lang,
            target_lang=target_lang,
        )

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<tmx version="1.4">',
            '  <body>',
        ]

        for entry in entries:
            src = entry.source_text.replace('&', '&amp;').replace('<', '&lt;')
            tgt = entry.target_text.replace('&', '&amp;').replace('<', '&lt;')
            lines.append(f'    <tu>')
            lines.append(f'      <tuv xml:lang="{source_lang}"><seg>{src}</seg></tuv>')
            lines.append(f'      <tuv xml:lang="{target_lang}"><seg>{tgt}</seg></tuv>')
            lines.append(f'    </tu>')

        lines.append('  </body>')
        lines.append('</tmx>')
        return '\n'.join(lines)
