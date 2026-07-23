import structlog
import requests
from django.conf import settings

logger = structlog.get_logger(__name__)

CHUNK_SIZE = 4500

STYLE_INSTRUCTIONS = {
    'faithful': 'Translate literally and precisely. Preserve the exact meaning and structure of the original text. Use formal, technical language.',
    'fluid': 'Translate naturally and readably. Use common expressions and natural sentence structures that flow well in the target language.',
    'creative': 'Translate creatively. Adapt the text for cultural context, use idiomatic expressions, and make it engaging for the target audience.',
    'formal': 'Translate in a formal business tone. Use polite, professional language suitable for official correspondence or reports.',
    'casual': 'Translate informally. Use conversational language, contractions, and a friendly tone as if speaking to a friend.',
}


def chunk_text(text: str, max_len: int = CHUNK_SIZE) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    paragraphs = text.split('\n\n')
    current = ''
    for para in paragraphs:
        if len(current) + len(para) + 2 > max_len:
            if current:
                chunks.append(current)
            if len(para) > max_len:
                words = para.split()
                current = ''
                for word in words:
                    if len(current) + len(word) + 1 > max_len:
                        if current:
                            chunks.append(current)
                        current = word
                    else:
                        current = f"{current} {word}".strip()
            else:
                current = para
        else:
            current = f"{current}\n\n{para}".strip() if current else para
    if current:
        chunks.append(current)
    return chunks


def translate_text(text: str, source: str = 'auto', target: str = 'en', style: str = 'fluid') -> str:
    if not text.strip():
        return text

    if source == 'auto':
        source = 'en'

    libre_supported = LibreTranslateService.is_supported(source, target)
    if libre_supported:
        try:
            result = LibreTranslateService.translate_text(text, source, target)
            return result.get('translatedText', text)
        except Exception as e:
            logger.warning("LibreTranslate failed (%s), trying Google Translate", e)

    try:
        result = GoogleTranslateService.translate_text(text, source, target)
        return result.get('translatedText', text)
    except Exception as e:
        logger.warning("Google Translate failed (%s), trying Ollama", e)
    try:
        result = OllamaTranslateService.translate_text(text, source, target, style=style)
        return result.get('translatedText', text)
    except Exception as e:
        logger.error("All translation services failed: %s", e)
        raise


def translate_document(text: str, source: str = 'auto', target: str = 'en', style: str = 'fluid') -> str:
    chunks = chunk_text(text)
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        logger.info("Translating chunk %d/%d", i + 1, len(chunks))
        translated = translate_text(chunk, source, target, style=style)
        translated_chunks.append(translated)
    return '\n\n'.join(translated_chunks)


class LibreTranslateService:
    _supported_langs: list[str] | None = None

    @classmethod
    def _fetch_supported(cls) -> list[str]:
        if cls._supported_langs is None:
            try:
                resp = requests.get(f"{settings.LIBRETRANSLATE_URL}/languages", timeout=10)
                resp.raise_for_status()
                cls._supported_langs = [lang['code'] for lang in resp.json()]
            except Exception:
                cls._supported_langs = ['en', 'hi', 'fr', 'de', 'es', 'it', 'ar', 'pt', 'ru', 'ja', 'ko', 'zh']
        return cls._supported_langs

    @classmethod
    def is_supported(cls, source: str, target: str) -> bool:
        langs = cls._fetch_supported()
        return source in langs and target in langs

    @staticmethod
    def translate_text(text: str, source: str = 'auto', target: str = 'en') -> dict:
        payload = {
            'q': text,
            'source': source,
            'target': target,
            'format': 'text',
        }
        headers = {'Content-Type': 'application/json'}
        if settings.LIBRETRANSLATE_API_KEY:
            headers['Authorization'] = f'Bearer {settings.LIBRETRANSLATE_API_KEY}'
            payload['api_key'] = settings.LIBRETRANSLATE_API_KEY
        response = requests.post(f"{settings.LIBRETRANSLATE_URL}/translate", json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        return response.json()


class GoogleTranslateService:
    @staticmethod
    def translate_text(text: str, source: str = 'en', target: str = 'en') -> dict:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=source, target=target)
        translated = translator.translate(text)
        return {
            'translatedText': translated,
            'source': source,
            'target': target,
        }


class OllamaTranslateService:
    LANG_MAP = {
        'en': 'English', 'fr': 'French', 'de': 'German', 'es': 'Spanish',
        'it': 'Italian', 'hi': 'Hindi', 'ar': 'Arabic', 'pt': 'Portuguese',
        'ru': 'Russian', 'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese',
        'nl': 'Dutch', 'pl': 'Polish', 'tr': 'Turkish', 'vi': 'Vietnamese',
        'th': 'Thai', 'id': 'Indonesian', 'sv': 'Swedish', 'da': 'Danish',
        'fi': 'Finnish', 'no': 'Norwegian', 'uk': 'Ukrainian', 'cs': 'Czech',
        'el': 'Greek', 'he': 'Hebrew', 'ro': 'Romanian', 'hu': 'Hungarian',
        'fa': 'Persian', 'ms': 'Malay', 'bn': 'Bengali', 'sw': 'Swahili',
        'ta': 'Tamil', 'te': 'Telugu', 'gu': 'Gujarati', 'ur': 'Urdu', 'tl': 'Tagalog',
        'ca': 'Catalan', 'eu': 'Basque', 'gl': 'Galician', 'af': 'Afrikaans',
    }

    @classmethod
    def _resolve_lang(cls, code: str) -> str:
        if code == 'auto':
            return 'the detected language'
        return cls.LANG_MAP.get(code, code)

    @classmethod
    def translate_text(cls, text: str, source: str = 'auto', target: str = 'en', style: str = 'fluid') -> dict:
        source_name = cls._resolve_lang(source)
        target_name = cls._resolve_lang(target)
        style_instruction = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS['fluid'])

        prompt = (
            f"Translate the following text from {source_name} to {target_name}.\n"
            f"Style: {style_instruction}\n"
            f"Output ONLY the translated text, nothing else.\n\n{text}"
        )

        response = requests.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={
                'model': settings.OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False,
            },
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        translated = data.get('response', '').strip()
        return {
            'translatedText': translated,
            'source': source,
            'target': target,
        }
