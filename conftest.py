import io
import tempfile

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import APIKey, UserProfile
from apps.billing.models import Plan, Subscription
from apps.documents.models import DocumentJob
from apps.glossaries.models import Glossary, GlossaryEntry
from apps.memory.models import TMEntry


@pytest.fixture
def user(db):
    u = User.objects.create_user(username="testuser", email="test@test.com", password="testpass123")
    UserProfile.objects.create(user=u, plan="free")
    return u


@pytest.fixture
def pro_user(db):
    u = User.objects.create_user(username="testpro", email="pro@test.com", password="testpass123")
    UserProfile.objects.create(user=u, plan="pro")
    return u


@pytest.fixture
def team_user(db):
    u = User.objects.create_user(username="testteam", email="team@test.com", password="testpass123")
    UserProfile.objects.create(user=u, plan="team")
    return u


@pytest.fixture
def enterprise_user(db):
    u = User.objects.create_user(username="testenterprise", email="enterprise@test.com", password="testpass123")
    UserProfile.objects.create(user=u, plan="enterprise")
    return u


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(username="admin", email="admin@test.com", password="adminpass123")


@pytest.fixture
def authenticated_client(client, user):
    client.login(username="testuser", password="testpass123")
    return client


@pytest.fixture
def pro_client(client, pro_user):
    client.login(username="testpro", password="testpass123")
    return client


@pytest.fixture
def admin_client(client, admin_user):
    client.login(username="admin", password="adminpass123")
    return client


@pytest.fixture
def sample_txt_file():
    content = b"This is a test document for translation.\nSecond line of text."
    return SimpleUploadedFile("test_document.txt", content, content_type="text/plain")


@pytest.fixture
def sample_pdf_file():
    content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
    return SimpleUploadedFile("test_document.pdf", content, content_type="application/pdf")


@pytest.fixture
def sample_docx_file():
    content = b"PK\x03\x04test docx content"
    return SimpleUploadedFile("test_document.docx", content, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@pytest.fixture
def sample_csv_glossary():
    content = b"source,target\nhello,namaste\nworld,sansar\ndocument,dastavej"
    return SimpleUploadedFile("glossary.csv", content, content_type="text/csv")


@pytest.fixture
def plan_free(db):
    return Plan.objects.create(
        name="Free", slug="free", price_monthly=0, price_yearly=0,
        max_documents_per_month=5, max_pages_per_document=10,
        max_characters_per_month=50000, features=["basic_translation"],
    )


@pytest.fixture
def plan_pro(db):
    return Plan.objects.create(
        name="Pro", slug="pro", price_monthly=19, price_yearly=190,
        max_documents_per_month=-1, max_pages_per_document=50,
        max_characters_per_month=-1, features=["pdf_layout", "glossary", "tm"],
    )


@pytest.fixture
def plan_team(db):
    return Plan.objects.create(
        name="Team", slug="team", price_monthly=49, price_yearly=490,
        max_documents_per_month=-1, max_pages_per_document=100,
        max_characters_per_month=-1, features=["pdf_layout", "glossary", "tm", "webhooks"],
    )


@pytest.fixture
def plan_enterprise(db):
    return Plan.objects.create(
        name="Enterprise", slug="enterprise", price_monthly=0, price_yearly=0,
        max_documents_per_month=-1, max_pages_per_document=9999,
        max_characters_per_month=-1, features=["all"],
    )


@pytest.fixture
def subscription(user, plan_free):
    return Subscription.objects.create(
        user=user, plan=plan_free, status="active",
    )


@pytest.fixture
def glossary(user):
    g = Glossary.objects.create(user=user, name="Test Glossary", source_lang="en", target_lang="hi")
    GlossaryEntry.objects.create(glossary=g, source="hello", target="namaste")
    GlossaryEntry.objects.create(glossary=g, source="world", target="sansar")
    return g


@pytest.fixture
def tm_entry(user):
    return TMEntry.objects.create(
        user=user, source_lang="en", target_lang="hi",
        source_text="Hello world", target_text="नमस्ते संसार",
        context="Greeting", quality_score=0.95,
    )


@pytest.fixture
def api_key(user):
    return APIKey.objects.create(user=user, name="Test Key", is_active=True, rate_limit=100)


@pytest.fixture
def document_job(sample_txt_file):
    return DocumentJob.objects.create(
        source_file=sample_txt_file,
        source_language="en",
        target_language="hi",
        status="completed",
    )
