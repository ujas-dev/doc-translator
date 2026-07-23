import structlog
from difflib import SequenceMatcher

logger = structlog.get_logger(__name__)


class QAScoringService:
    @staticmethod
    def score_length_consistency(source: str, translation: str) -> dict:
        src_len = len(source)
        tgt_len = len(translation)
        if src_len == 0:
            return {'score': 1.0, 'details': {'reason': 'empty_source'}}
        ratio = tgt_len / src_len
        if 0.5 <= ratio <= 2.0:
            score = 1.0
        elif 0.3 <= ratio <= 3.0:
            score = 0.7
        else:
            score = 0.3
        return {'score': score, 'details': {'source_len': src_len, 'target_len': tgt_len, 'ratio': round(ratio, 2)}}

    @staticmethod
    def score_term_consistency(source: str, translation: str, glossary_terms: dict = None) -> dict:
        if not glossary_terms:
            return {'score': 1.0, 'details': {'reason': 'no_glossary'}}
        source_lower = source.lower()
        found = 0
        total = len(glossary_terms)
        for term, expected in glossary_terms.items():
            if term.lower() in source_lower:
                found += 1
        score = found / total if total > 0 else 1.0
        return {'score': score, 'details': {'total_terms': total, 'found_in_source': found}}

    @staticmethod
    def score_empty_segments(segments: list) -> dict:
        if not segments:
            return {'score': 1.0, 'details': {'reason': 'no_segments'}}
        empty_count = sum(1 for s in segments if not s.strip())
        score = 1.0 - (empty_count / len(segments))
        return {'score': score, 'details': {'total_segments': len(segments), 'empty_segments': empty_count}}

    @staticmethod
    def score_untranslated(source: str, translation: str) -> dict:
        source_lower = source.lower().strip()
        translation_lower = translation.lower().strip()
        similarity = SequenceMatcher(None, source_lower, translation_lower).ratio()
        if similarity > 0.9:
            score = 0.5
        elif similarity > 0.7:
            score = 0.7
        else:
            score = 1.0
        return {'score': score, 'details': {'similarity': round(similarity, 3)}}

    @classmethod
    def run_all_checks(cls, source: str, translation: str, glossary_terms: dict = None, segments: list = None) -> dict:
        results = {}
        results['length_consistency'] = cls.score_length_consistency(source, translation)
        results['term_consistency'] = cls.score_term_consistency(source, translation, glossary_terms)
        results['untranslated'] = cls.score_untranslated(source, translation)
        if segments:
            results['empty_segments'] = cls.score_empty_segments(segments)
        weights = {'length_consistency': 0.3, 'term_consistency': 0.3, 'untranslated': 0.3, 'empty_segments': 0.1}
        total_weight = sum(weights.get(k, 0) for k in results)
        weighted_sum = sum(results[k]['score'] * weights.get(k, 0) for k in results)
        overall = weighted_sum / total_weight if total_weight > 0 else 1.0
        results['overall'] = {'score': round(overall, 3), 'details': {}}
        return results
