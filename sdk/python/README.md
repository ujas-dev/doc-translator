# Doc Translator Python SDK

A Python client library for the Doc Translator API.

## Installation

```bash
pip install doc-translator
```

Or install from source:

```bash
git clone https://github.com/doctranslator/python-sdk.git
cd python-sdk
pip install -e .
```

## Quick Start

```python
from doc_translator import DocTranslatorClient

# Initialize the client
client = DocTranslatorClient(
    api_key="your-api-key",
    base_url="http://localhost:8000"  # Your Doc Translator instance
)

# Translate a file
job = client.create_job(
    file_path="document.pdf",
    source_lang="en",
    target_lang="hi",
    style="faithful"
)

# Wait for completion
result = client.wait_for_completion(job['pk'])

# Download the translated file
client.download_output(job['pk'], "translated.pdf")
```

## Convenience Function

```python
from doc_translator import translate_document

translate_document(
    file_path="document.pdf",
    output_path="translated.pdf",
    api_key="your-api-key",
    source_lang="en",
    target_lang="hi"
)
```

## API Reference

### DocTranslatorClient

#### `__init__(api_key, base_url="http://localhost:8000")`

Initialize the client with your API key.

#### `create_job(file_path, source_lang, target_lang, style, bilingual, glossary_id)`

Create a new translation job.

**Parameters:**
- `file_path` (str): Path to the file to translate
- `source_lang` (str): Source language code (default: "en")
- `target_lang` (str): Target language code (default: "hi")
- `style` (str): Translation style - faithful, fluid, creative, formal, casual
- `bilingual` (bool): Create bilingual output (default: False)
- `glossary_id` (int): Optional glossary ID to use

**Returns:** Job details dictionary

#### `get_job(job_id)`

Get job status and details.

#### `list_jobs(limit=50)`

List recent jobs.

#### `download_output(job_id, output_path)`

Download the translated file.

#### `wait_for_completion(job_id, timeout=300, poll_interval=2)`

Wait for a job to complete. Raises `TimeoutError` or `RuntimeError` on failure.

#### `translate_file(file_path, output_path, ...)`

Translate a file and download the result (combines create + wait + download).

#### `get_glossaries()`

Get list of glossaries.

#### `get_translation_memory(text, source_lang, target_lang)`

Search translation memory for matching translations.

## Supported Languages

The API supports all languages available in your Doc Translator instance. Common language codes:

- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `hi` - Hindi
- `ar` - Arabic
- `ja` - Japanese
- `zh` - Chinese

## Error Handling

```python
from doc_translator import DocTranslatorClient
import requests

client = DocTranslatorClient(api_key="your-api-key")

try:
    job = client.create_job("document.pdf")
except requests.exceptions.HTTPError as e:
    print(f"API error: {e}")

try:
    result = client.wait_for_completion(job['pk'], timeout=60)
except TimeoutError:
    print("Translation took too long")
except RuntimeError as e:
    print(f"Translation failed: {e}")
```

## License

MIT License
