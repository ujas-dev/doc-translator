import pytest
from django.contrib.auth.models import User
from apps.accounts.forms import RegisterForm


class TestRegisterFormValidation:
    def test_valid_form(self):
        form = RegisterForm(data={
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        assert form.is_valid()

    def test_duplicate_email_rejected(self, user):
        form = RegisterForm(data={
            'username': 'anotheruser',
            'email': 'test@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_mismatched_passwords(self):
        form = RegisterForm(data={
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'StrongPass123!',
            'password2': 'DifferentPass456!',
        })
        assert not form.is_valid()

    def test_missing_email(self):
        form = RegisterForm(data={
            'username': 'newuser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_duplicate_username(self, user):
        form = RegisterForm(data={
            'username': 'testuser',
            'email': 'different@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        assert not form.is_valid()
        assert 'username' in form.errors
