import secrets
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import APIKey, UserProfile
from apps.billing.models import Plan, Subscription
from apps.glossaries.models import Glossary, GlossaryEntry
from apps.memory.models import TMEntry


PLANS = [
    {"name": "Free", "slug": "free", "price_monthly": 0, "price_yearly": 0,
     "max_documents_per_month": 5, "max_pages_per_document": 10,
     "max_characters_per_month": 50000, "features": ["basic_translation"]},
    {"name": "Pro", "slug": "pro", "price_monthly": 19, "price_yearly": 190,
     "max_documents_per_month": -1, "max_pages_per_document": 50,
     "max_characters_per_month": -1, "features": ["pdf_layout", "glossary", "tm", "api_access"]},
    {"name": "Team", "slug": "team", "price_monthly": 49, "price_yearly": 490,
     "max_documents_per_month": -1, "max_pages_per_document": 100,
     "max_characters_per_month": -1, "features": ["pdf_layout", "glossary", "tm", "api_access", "webhooks", "batch"]},
    {"name": "Enterprise", "slug": "enterprise", "price_monthly": 0, "price_yearly": 0,
     "max_documents_per_month": -1, "max_pages_per_document": 9999,
     "max_characters_per_month": -1, "features": ["all", "sso", "audit_logs", "sla"]},
]

USERS = [
    {"username": "free_user", "plan": "free", "docs_used": 3, "rich": False},
    {"username": "free_user2", "plan": "free", "docs_used": 0, "rich": False},
    {"username": "pro_user", "plan": "pro", "docs_used": 0, "rich": True},
    {"username": "pro_user2", "plan": "pro", "docs_used": 0, "rich": False},
    {"username": "team_user", "plan": "team", "docs_used": 0, "rich": True},
    {"username": "team_user2", "plan": "team", "docs_used": 0, "rich": False},
    {"username": "enterprise_user", "plan": "enterprise", "docs_used": 0, "rich": True},
    {"username": "enterprise_user2", "plan": "enterprise", "docs_used": 0, "rich": False},
]

PASSWORD = "testpass123"


class Command(BaseCommand):
    help = "Create test users for each plan tier with realistic data"

    def handle(self, *args, **options):
        self.stdout.write("Creating plans...")
        plans = {}
        for plan_data in PLANS:
            plan, _ = Plan.objects.update_or_create(
                slug=plan_data["slug"],
                defaults=plan_data,
            )
            plans[plan.slug] = plan
            self.stdout.write(f"  Plan: {plan.name} (${plan.price_monthly}/mo)")

        self.stdout.write("\nCreating users...")
        for user_data in USERS:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": f"{user_data['username']}@test.com",
                    "first_name": user_data["username"].replace("_", " ").title(),
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
                self.stdout.write(f"  Created: {user.username}")
            else:
                self.stdout.write(f"  Exists:  {user.username}")

            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={"plan": user_data["plan"]},
            )
            profile.plan = user_data["plan"]
            profile.documents_used_this_month = user_data["docs_used"]
            profile.save()

            plan = plans[user_data["plan"]]
            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    "plan": plan,
                    "status": "active",
                    "current_period_start": timezone.now(),
                    "current_period_end": timezone.now() + timedelta(days=30),
                },
            )

            if user_data["rich"]:
                self._create_rich_data(user, user_data["plan"])

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created {len(USERS)} users with password: {PASSWORD}"
        ))

    def _create_rich_data(self, user, plan_slug):
        APIKey.objects.get_or_create(
            user=user,
            name=f"{plan_slug.title()} API Key",
            defaults={
                "key": secrets.token_hex(32),
                "is_active": True,
                "rate_limit": 100 if plan_slug == "pro" else (500 if plan_slug == "team" else 1000),
            },
        )

        glossary, _ = Glossary.objects.get_or_create(
            user=user,
            name=f"General {plan_slug.title()} Glossary",
            defaults={"source_lang": "en", "target_lang": "hi", "description": "Test glossary"},
        )
        for src, tgt in [("hello", "namaste"), ("world", "sansar"), ("document", "dastavej")]:
            GlossaryEntry.objects.get_or_create(
                glossary=glossary, source=src, defaults={"target": tgt}
            )

        if plan_slug in ("team", "enterprise"):
            g2, _ = Glossary.objects.get_or_create(
                user=user,
                name="Technical Terms",
                defaults={"source_lang": "en", "target_lang": "gu", "description": "Tech glossary"},
            )
            for src, tgt in [("software", "software"), ("computer", "computer"), ("internet", "internet")]:
                GlossaryEntry.objects.get_or_create(
                    glossary=g2, source=src, defaults={"target": tgt}
                )

        tm_count = 5 if plan_slug == "pro" else (10 if plan_slug == "team" else 20)
        for i in range(tm_count):
            TMEntry.objects.get_or_create(
                user=user,
                source_text=f"Source sentence {i} for testing translation memory",
                source_lang="en",
                target_lang="hi",
                defaults={
                    "target_text": f"परीक्षण अनुवाद स्मृति के लिए स्रोत वाक्य {i}",
                    "context": f"Test context {i}",
                    "quality_score": 0.9,
                },
            )
