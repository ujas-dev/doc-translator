import csv
import io
from .models import Glossary, GlossaryEntry


class GlossaryService:
    @staticmethod
    def create_glossary(user, name, source_lang='en', target_lang='hi', description=''):
        return Glossary.objects.create(
            user=user,
            name=name,
            source_lang=source_lang,
            target_lang=target_lang,
            description=description,
        )

    @staticmethod
    def add_entry(glossary, source, target, context='', is_preferred=False):
        return GlossaryEntry.objects.create(
            glossary=glossary,
            source=source,
            target=target,
            context=context,
            is_preferred=is_preferred,
        )

    @staticmethod
    def import_csv(glossary, file_content: str) -> dict:
        reader = csv.DictReader(io.StringIO(file_content))
        created = 0
        skipped = 0

        for row in reader:
            source = row.get('source', row.get('Source', '')).strip()
            target = row.get('target', row.get('Target', '')).strip()
            if source and target:
                _, was_created = GlossaryEntry.objects.get_or_create(
                    glossary=glossary,
                    source=source,
                    defaults={'target': target},
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        return {"created": created, "skipped": skipped}

    @staticmethod
    def export_csv(glossary) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['source', 'target', 'context', 'is_preferred'])
        writer.writeheader()

        for entry in glossary.entries.all():
            writer.writerow({
                'source': entry.source,
                'target': entry.target,
                'context': entry.context,
                'is_preferred': entry.is_preferred,
            })

        return output.getvalue()

    @staticmethod
    def apply_glossary(text: str, glossary) -> str:
        entries = glossary.entries.order_by('-source')
        for entry in entries:
            text = text.replace(entry.source, entry.target)
        return text

    @staticmethod
    def get_matches(text: str, glossary, threshold: float = 0.8) -> list:
        matches = []
        for entry in glossary.entries.all():
            if entry.source.lower() in text.lower():
                matches.append({
                    "source": entry.source,
                    "target": entry.target,
                    "context": entry.context,
                    "is_preferred": entry.is_preferred,
                    "match_type": "exact",
                })
        return matches

    @staticmethod
    def suggest_terms(text: str, glossary) -> list:
        suggestions = []
        text_lower = text.lower()
        for entry in glossary.entries.all():
            count = text_lower.count(entry.source.lower())
            if count > 0:
                suggestions.append({
                    "source": entry.source,
                    "target": entry.target,
                    "context": entry.context,
                    "is_preferred": entry.is_preferred,
                    "match_type": "exact",
                    "frequency": count,
                })
        return sorted(suggestions, key=lambda x: x['frequency'], reverse=True)
