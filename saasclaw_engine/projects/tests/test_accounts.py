"""Tests for user accounts — model, auth, permissions."""
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTests(TestCase):
    """Test User model basics."""

    def test_create_user(self):
        user = User.objects.create_user(username='alice', password='***')
        assert user.username == 'alice'
        assert user.check_password('***')
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username='admin', password='admin123', email='admin@test.com'
        )
        assert user.is_staff
        assert user.is_superuser
        assert user.email == 'admin@test.com'

    def test_user_str(self):
        user = User(username='bob')
        assert str(user) == 'bob'

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='dup', password='***')
        with self.assertRaises(Exception):  # IntegrityError
            User.objects.create_user(username='dup', password='***')

    def test_password_not_stored_plain(self):
        user = User.objects.create_user(username='secure', password='***')
        # Password should be hashed, not plaintext
        assert user.password.startswith('pbkdf2_') or user.password.startswith('argon2')

    def test_check_password(self):
        user = User.objects.create_user(username='check', password='correct-horse')
        assert user.check_password('correct-horse')
        assert not user.check_password('wrong')


class AuthBackendTests(TestCase):
    """Test that Django's auth backend works with our users."""

    def test_authenticate_with_username(self):
        User.objects.create_user(username='authuser', password='***')
        from django.contrib.auth import authenticate
        user = authenticate(username='authuser', password='***')
        assert user is not None
        assert user.username == 'authuser'

    def test_authenticate_wrong_password(self):
        User.objects.create_user(username='wrongpw', password='***')
        from django.contrib.auth import authenticate
        user = authenticate(username='wrongpw', password='wrong')
        assert user is None

    def test_authenticate_nonexistent_user(self):
        from django.contrib.auth import authenticate
        user = authenticate(username='ghost', password='anything')
        assert user is None
