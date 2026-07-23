import secrets
from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('team', 'Team'),
        ('enterprise', 'Enterprise'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    documents_used_this_month = models.IntegerField(default=0)
    characters_used_this_month = models.IntegerField(default=0)
    monthly_reset_date = models.DateField(auto_now_add=True)
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.plan})"

    @property
    def can_translate(self):
        if self.plan == 'pro':
            return True
        if self.plan == 'team':
            return True
        if self.plan == 'enterprise':
            return True
        return self.documents_used_this_month < 5

    @property
    def max_pages_per_document(self):
        limits = {'free': 10, 'pro': 50, 'team': 100, 'enterprise': 9999}
        return limits.get(self.plan, 10)

    PLAN_FEATURES = {
        'free': [],
        'pro': ['glossary', 'tm', 'qa', 'api_access', 'pdf_layout'],
        'team': ['glossary', 'tm', 'qa', 'api_access', 'pdf_layout', 'batch', 'teams', 'webhooks', 'audit'],
        'enterprise': ['glossary', 'tm', 'qa', 'api_access', 'pdf_layout', 'batch', 'teams', 'webhooks', 'audit', 'sso'],
    }

    def has_feature(self, feature):
        features = self.PLAN_FEATURES.get(self.plan, [])
        return feature in features


class APIKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    rate_limit = models.IntegerField(default=100, help_text="Requests per hour")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.key[:8]}...)"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_hex(32)
        super().save(*args, **kwargs)

    @property
    def masked_key(self):
        return f"{self.key[:8]}...{self.key[-4:]}"
