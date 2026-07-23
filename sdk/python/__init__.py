"""
Doc Translator Python SDK

Usage:
    from doc_translator import DocTranslatorClient, translate_document

    # Using the client
    client = DocTranslatorClient(api_key="your-api-key")
    job = client.create_job("document.pdf", source_lang="en", target_lang="hi")
    result = client.wait_for_completion(job['pk'])
    client.download_output(job['pk'], "translated.pdf")

    # Using the convenience function
    translate_document(
        file_path="document.pdf",
        output_path="translated.pdf",
        api_key="your-api-key",
        source_lang="en",
        target_lang="hi",
    )
"""

from .doc_translator import DocTranslatorClient, translate_document

__all__ = ['DocTranslatorClient', 'translate_document']
__version__ = '1.0.0'
