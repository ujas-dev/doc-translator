"""
Doc Translator Python SDK

A Python client for the Doc Translator API.
"""

import os
import time
import requests
from typing import Optional, BinaryIO


class DocTranslatorClient:
    """Client for the Doc Translator API."""

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        """
        Initialize the client.

        Args:
            api_key: Your API key
            base_url: Base URL of the Doc Translator instance
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Api-Key {api_key}',
        })

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def create_job(
        self,
        file_path: str,
        source_lang: str = 'en',
        target_lang: str = 'hi',
        style: str = 'faithful',
        bilingual: bool = False,
        glossary_id: Optional[int] = None,
    ) -> dict:
        """
        Create a new translation job.

        Args:
            file_path: Path to the file to translate
            source_lang: Source language code
            target_lang: Target language code
            style: Translation style (faithful, fluid, creative, formal, casual)
            bilingual: Whether to create bilingual output
            glossary_id: Optional glossary ID to use

        Returns:
            Job details dictionary
        """
        with open(file_path, 'rb') as f:
            files = {'source_file': (os.path.basename(file_path), f)}
            data = {
                'source_language': source_lang,
                'target_language': target_lang,
                'style': style,
                'bilingual': str(bilingual).lower(),
            }
            if glossary_id:
                data['glossary'] = glossary_id

            response = self.session.post(self._url('/api/jobs/'), files=files, data=data)
            response.raise_for_status()
            return response.json()

    def get_job(self, job_id: int) -> dict:
        """
        Get job status and details.

        Args:
            job_id: Job ID

        Returns:
            Job details dictionary
        """
        response = self.session.get(self._url(f'/api/jobs/{job_id}/'))
        response.raise_for_status()
        return response.json()

    def list_jobs(self, limit: int = 50) -> list:
        """
        List recent jobs.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of job dictionaries
        """
        response = self.session.get(self._url('/api/jobs/'), params={'limit': limit})
        response.raise_for_status()
        return response.json()

    def download_output(self, job_id: int, output_path: str) -> str:
        """
        Download the translated file.

        Args:
            job_id: Job ID
            output_path: Path to save the downloaded file

        Returns:
            Path to the downloaded file
        """
        response = self.session.get(
            self._url(f'/api/jobs/{job_id}/download/'),
            stream=True
        )
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return output_path

    def wait_for_completion(
        self,
        job_id: int,
        timeout: int = 300,
        poll_interval: int = 2,
    ) -> dict:
        """
        Wait for a job to complete.

        Args:
            job_id: Job ID
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds

        Returns:
            Final job details dictionary

        Raises:
            TimeoutError: If job doesn't complete within timeout
            RuntimeError: If job fails
        """
        start_time = time.time()

        while True:
            job = self.get_job(job_id)
            status = job.get('status')

            if status == 'completed':
                return job
            elif status == 'failed':
                raise RuntimeError(f"Job failed: {job.get('error_message', 'Unknown error')}")

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

            time.sleep(poll_interval)

    def translate_file(
        self,
        file_path: str,
        output_path: str,
        source_lang: str = 'en',
        target_lang: str = 'hi',
        style: str = 'faithful',
        bilingual: bool = False,
        glossary_id: Optional[int] = None,
        timeout: int = 300,
    ) -> str:
        """
        Translate a file and download the result.

        Args:
            file_path: Path to the file to translate
            output_path: Path to save the translated file
            source_lang: Source language code
            target_lang: Target language code
            style: Translation style
            bilingual: Whether to create bilingual output
            glossary_id: Optional glossary ID to use
            timeout: Maximum time to wait for completion

        Returns:
            Path to the translated file
        """
        job = self.create_job(
            file_path=file_path,
            source_lang=source_lang,
            target_lang=target_lang,
            style=style,
            bilingual=bilingual,
            glossary_id=glossary_id,
        )

        job_id = job['pk']
        self.wait_for_completion(job_id, timeout=timeout)

        return self.download_output(job_id, output_path)

    def get_glossaries(self) -> list:
        """
        Get list of glossaries.

        Returns:
            List of glossary dictionaries
        """
        response = self.session.get(self._url('/glossaries/'))
        response.raise_for_status()
        return response.json()

    def get_translation_memory(
        self,
        text: str,
        source_lang: str = 'en',
        target_lang: str = 'hi',
    ) -> dict:
        """
        Search translation memory.

        Args:
            text: Text to search for
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Matching translations
        """
        response = self.session.get(
            self._url('/tm/leverage/'),
            params={
                'text': text,
                'source_lang': source_lang,
                'target_lang': target_lang,
            }
        )
        response.raise_for_status()
        return response.json()

    def get_usage(self) -> dict:
        """
        Get current usage statistics.

        Returns:
            Usage statistics dictionary
        """
        response = self.session.get(self._url('/api/jobs/'))
        response.raise_for_status()
        data = response.json()

        return {
            'total_jobs': len(data),
            'jobs': data,
        }


def translate_document(
    file_path: str,
    output_path: str,
    api_key: str,
    base_url: str = "http://localhost:8000",
    source_lang: str = 'en',
    target_lang: str = 'hi',
    style: str = 'faithful',
    bilingual: bool = False,
) -> str:
    """
    Convenience function to translate a document.

    Args:
        file_path: Path to the file to translate
        output_path: Path to save the translated file
        api_key: Your API key
        base_url: Base URL of the Doc Translator instance
        source_lang: Source language code
        target_lang: Target language code
        style: Translation style
        bilingual: Whether to create bilingual output

    Returns:
        Path to the translated file
    """
    client = DocTranslatorClient(api_key=api_key, base_url=base_url)
    return client.translate_file(
        file_path=file_path,
        output_path=output_path,
        source_lang=source_lang,
        target_lang=target_lang,
        style=style,
        bilingual=bilingual,
    )
