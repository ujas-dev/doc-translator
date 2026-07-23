from unittest.mock import patch, MagicMock

import pytest

from apps.translation.services import (
    LibreTranslateService,
    GoogleTranslateService,
    OllamaTranslateService,
    translate_text,
    translate_document,
    STYLE_INSTRUCTIONS,
)


class TestStyleInstructions:
    def test_all_styles_defined(self):
        expected_styles = ['faithful', 'fluid', 'creative', 'formal', 'casual']
        for style in expected_styles:
            assert style in STYLE_INSTRUCTIONS, f"Missing style: {style}"

    def test_instructions_are_strings(self):
        for style, instruction in STYLE_INSTRUCTIONS.items():
            assert isinstance(instruction, str)
            assert len(instruction) > 0


class TestLibreTranslateService:
    @patch("apps.translation.services.requests.get")
    def test_get_supported_languages(self, mock_get):
        LibreTranslateService._supported_langs = None
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {"code": "en", "name": "English"},
            {"code": "hi", "name": "Hindi"},
        ]
        mock_get.return_value = mock_resp
        langs = LibreTranslateService._fetch_supported()
        assert "en" in langs
        assert "hi" in langs
        LibreTranslateService._supported_langs = None

    @patch("apps.translation.services.requests.post")
    def test_translate_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"translatedText": "नमस्ते दुनिया"}
        mock_post.return_value = mock_resp
        result = LibreTranslateService.translate_text("Hello world", source="en", target="hi")
        assert result["translatedText"] == "नमस्ते दुनिया"

    @patch("apps.translation.services.requests.post")
    def test_translate_failure(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = Exception("Server error")
        mock_post.return_value = mock_resp
        with pytest.raises(Exception):
            LibreTranslateService.translate_text("Hello", source="en", target="hi")

    def test_is_supported(self):
        LibreTranslateService._supported_langs = ["en", "hi", "fr"]
        assert LibreTranslateService.is_supported("en", "hi") is True
        assert LibreTranslateService.is_supported("en", "gu") is False
        LibreTranslateService._supported_langs = None


class TestGoogleTranslateService:
    @patch("deep_translator.GoogleTranslator")
    def test_translate_success(self, mock_cls):
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "नमस्ते दुनिया"
        mock_cls.return_value = mock_instance
        result = GoogleTranslateService.translate_text("Hello world", source="en", target="hi")
        assert result["translatedText"] == "नमस्ते दुनिया"

    @patch("deep_translator.GoogleTranslator")
    def test_translate_exception(self, mock_cls):
        mock_cls.side_effect = Exception("API Error")
        with pytest.raises(Exception):
            GoogleTranslateService.translate_text("Hello", source="en", target="hi")


class TestOllamaTranslateService:
    @patch("apps.translation.services.requests.post")
    def test_translate_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"response": "नमस्ते दुनिया"}
        mock_post.return_value = mock_resp
        result = OllamaTranslateService.translate_text("Hello world", source="en", target="hi")
        assert result["translatedText"] == "नमस्ते दुनिया"

    @patch("apps.translation.services.requests.post")
    def test_translate_with_style(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"response": "translated"}
        mock_post.return_value = mock_resp
        result = OllamaTranslateService.translate_text("Hello", source="en", target="hi", style="formal")
        assert result["translatedText"] == "translated"
        call_args = mock_post.call_args
        prompt = call_args[1]['json']['prompt']
        assert STYLE_INSTRUCTIONS['formal'] in prompt

    @patch("apps.translation.services.requests.post")
    def test_translate_timeout(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        with pytest.raises(requests.exceptions.Timeout):
            OllamaTranslateService.translate_text("Hello", source="en", target="hi")

    def test_resolve_lang(self):
        assert OllamaTranslateService._resolve_lang("en") == "English"
        assert OllamaTranslateService._resolve_lang("hi") == "Hindi"
        assert OllamaTranslateService._resolve_lang("auto") == "the detected language"


class TestTranslateTextFallback:
    @patch("apps.translation.services.LibreTranslateService.translate_text", side_effect=Exception("fail"))
    @patch("apps.translation.services.GoogleTranslateService.translate_text", return_value={"translatedText": "google result"})
    def test_falls_through_to_google(self, mock_google, mock_libre):
        result = translate_text("Hello", source="en", target="hi")
        assert result == "google result"
        mock_google.assert_called_once()

    @patch("apps.translation.services.LibreTranslateService.is_supported", return_value=True)
    @patch("apps.translation.services.LibreTranslateService.translate_text", return_value={"translatedText": "libre result"})
    def test_uses_libre_first(self, mock_libre, mock_supported):
        result = translate_text("Hello", source="en", target="hi")
        assert result == "libre result"

    @patch("apps.translation.services.LibreTranslateService.is_supported", return_value=False)
    @patch("apps.translation.services.GoogleTranslateService.translate_text", side_effect=Exception("fail"))
    @patch("apps.translation.services.OllamaTranslateService.translate_text", side_effect=Exception("fail"))
    def test_all_fail_raises(self, mock_ollama, mock_google, mock_libre):
        with pytest.raises(Exception):
            translate_text("Hello", source="en", target="hi")

    @patch("apps.translation.services.LibreTranslateService.is_supported", return_value=True)
    @patch("apps.translation.services.LibreTranslateService.translate_text", side_effect=Exception("fail"))
    @patch("apps.translation.services.GoogleTranslateService.translate_text", side_effect=Exception("fail"))
    @patch("apps.translation.services.OllamaTranslateService.translate_text", return_value={"translatedText": "ollama result"})
    def test_falls_through_to_ollama(self, mock_ollama, mock_google, mock_libre, mock_supported):
        result = translate_text("Hello", source="en", target="hi")
        assert result == "ollama result"

    def test_empty_text(self):
        result = translate_text("", source="en", target="hi")
        assert result == ""


class TestStyleParameterPassthrough:
    @patch("apps.translation.services.LibreTranslateService.is_supported", return_value=True)
    @patch("apps.translation.services.LibreTranslateService.translate_text", return_value={"translatedText": "result"})
    def test_style_passed_to_libre(self, mock_libre, mock_supported):
        result = translate_text("Hello", source="en", target="hi", style="formal")
        assert result == "result"

    @patch("apps.translation.services.LibreTranslateService.is_supported", return_value=False)
    @patch("apps.translation.services.GoogleTranslateService.translate_text", return_value={"translatedText": "result"})
    def test_style_passed_to_google(self, mock_google, mock_supported):
        result = translate_text("Hello", source="en", target="hi", style="creative")
        assert result == "result"

    @patch("apps.translation.services.LibreTranslateService.is_supported", return_value=False)
    @patch("apps.translation.services.GoogleTranslateService.translate_text", side_effect=Exception("fail"))
    @patch("apps.translation.services.OllamaTranslateService.translate_text", return_value={"translatedText": "result"})
    def test_style_passed_to_ollama(self, mock_ollama, mock_google, mock_supported):
        result = translate_text("Hello", source="en", target="hi", style="casual")
        assert result == "result"
        assert mock_ollama.call_args[1].get('style') == 'casual'


class TestTranslateDocumentStyle:
    @patch("apps.translation.services.translate_text", return_value="translated chunk")
    def test_document_with_style(self, mock_translate):
        big_text = "word " * 5000
        result = translate_document(big_text, source="en", target="hi", style="formal")
        assert mock_translate.call_count > 1
        for call in mock_translate.call_args_list:
            assert call[1].get('style') == 'formal'

    @patch("apps.translation.services.translate_text", return_value="ok")
    def test_single_chunk_style(self, mock_translate):
        result = translate_document("short text", source="en", target="hi", style="formal")
        assert result == "ok"
        assert mock_translate.call_count == 1
        assert mock_translate.call_args[1].get('style') == 'formal'
