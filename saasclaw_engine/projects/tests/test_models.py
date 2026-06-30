"""Tests for Project model methods.

Covers: form_api_key generation, uniqueness, idempotency, and basic model fields.
"""

import pytest
from django.contrib.auth import get_user_model

from saasclaw_engine.projects.models import Project

User = get_user_model()


@pytest.mark.django_db
class TestProjectFormApiKey:
    """Tests for Project.get_or_create_form_api_key()."""

    def test_generates_key_when_blank(self):
        project = Project.objects.create(
            owner=User.objects.create_user("u1"),
            name="Test",
            slug="test-proj",
            workspace_root="/tmp/test",
            preview_domain="test.saasclaw.ai",
            production_domain="test.saasclaw.com",
        )
        assert project.form_api_key == ""
        key = project.get_or_create_form_api_key()
        assert key
        assert len(key) > 20
        # Reload from DB
        project.refresh_from_db()
        assert project.form_api_key == key

    def test_returns_existing_key(self):
        project = Project.objects.create(
            owner=User.objects.create_user("u2"),
            name="Test2",
            slug="test-proj-2",
            workspace_root="/tmp/test2",
            preview_domain="test2.saasclaw.ai",
            production_domain="test2.saasclaw.com",
            form_api_key="existing-key-123",
        )
        key = project.get_or_create_form_api_key()
        assert key == "existing-key-123"

    def test_key_is_different_across_projects(self):
        u = User.objects.create_user("u3")
        p1 = Project.objects.create(
            owner=u, name="A", slug="a",
            workspace_root="/tmp/a", preview_domain="a.x", production_domain="a.y",
        )
        p2 = Project.objects.create(
            owner=u, name="B", slug="b",
            workspace_root="/tmp/b", preview_domain="b.x", production_domain="b.y",
        )
        k1 = p1.get_or_create_form_api_key()
        k2 = p2.get_or_create_form_api_key()
        assert k1 != k2

    def test_key_is_idempotent(self):
        project = Project.objects.create(
            owner=User.objects.create_user("u4"),
            name="Test3",
            slug="test-proj-3",
            workspace_root="/tmp/test3",
            preview_domain="test3.saasclaw.ai",
            production_domain="test3.saasclaw.com",
        )
        k1 = project.get_or_create_form_api_key()
        k2 = project.get_or_create_form_api_key()
        assert k1 == k2

    def test_key_length_within_field_limit(self):
        project = Project.objects.create(
            owner=User.objects.create_user("u5"),
            name="Test4",
            slug="test-proj-4",
            workspace_root="/tmp/test4",
            preview_domain="test4.saasclaw.ai",
            production_domain="test4.saasclaw.com",
        )
        key = project.get_or_create_form_api_key()
        # token_urlsafe(40) produces ~53 chars, field is max_length=64
        assert len(key) <= 64


@pytest.mark.django_db
class TestProjectModel:
    """Basic model field tests."""

    def test_slug_uniqueness(self):
        u = User.objects.create_user("u6")
        Project.objects.create(
            owner=u, name="First", slug="dup",
            workspace_root="/tmp/dup1", preview_domain="d1.x", production_domain="d1.y",
        )
        with pytest.raises(Exception):
            Project.objects.create(
                owner=u, name="Second", slug="dup",
                workspace_root="/tmp/dup2", preview_domain="d2.x", production_domain="d2.y",
            )

    def test_default_values(self):
        project = Project.objects.create(
            owner=User.objects.create_user("u7"),
            name="Defaults",
            slug="defaults",
            workspace_root="/tmp/def",
            preview_domain="def.x",
            production_domain="def.y",
        )
        assert project.framework == "html"
        assert project.form_api_key == ""
        assert project.notes == ""
        assert project.description == ""

    def test_string_representation(self):
        project = Project.objects.create(
            owner=User.objects.create_user("u8"),
            name="My Project",
            slug="my-project",
            workspace_root="/tmp/my",
            preview_domain="my.x",
            production_domain="my.y",
        )
        assert str(project) == "My Project"
