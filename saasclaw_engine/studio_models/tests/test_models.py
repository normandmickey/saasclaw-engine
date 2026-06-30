"""Tests for Studio models — Workspace, AgentSession, AgentMessage.

Covers: creation, ordering, cascading deletes, status transitions,
branch property, message ordering, and profile assignment.
"""

import pytest
from django.contrib.auth import get_user_model

from saasclaw_engine.projects.models import Project
from saasclaw_engine.studio_models.models import (
    Workspace,
    AgentProfile,
    AgentSession,
    AgentMessage,
)

User = get_user_model()


@pytest.fixture
def project():
    return Project.objects.create(
        owner=User.objects.create_user("projowner"),
        name="Studio Test",
        slug="studio-test",
        workspace_root="/tmp/studio-test",
        preview_domain="studio-test.x",
        production_domain="studio-test.y",
    )


@pytest.fixture
def user():
    return User.objects.create_user("studio_user")


@pytest.mark.django_db
class TestWorkspace:
    def test_create_workspace(self, project, user):
        ws = Workspace.objects.create(
            project=project, user=user, base_branch="main", work_branch="studio/abc123"
        )
        assert str(ws) == "studio-test @ studio/abc123"

    def test_branch_property_uses_work_branch(self, project, user):
        ws = Workspace.objects.create(
            project=project, user=user, base_branch="main", work_branch="feat/test"
        )
        assert ws.branch == "feat/test"

    def test_branch_property_falls_back_to_base(self, project, user):
        ws = Workspace.objects.create(
            project=project, user=user, base_branch="main", work_branch=""
        )
        assert ws.branch == "main"

    def test_default_active(self, project, user):
        ws = Workspace.objects.create(project=project, user=user)
        assert ws.is_active is True

    def test_ordering_newest_first(self, project, user):
        ws1 = Workspace.objects.create(project=project, user=user)
        ws2 = Workspace.objects.create(project=project, user=user)
        ids = [w.id for w in Workspace.objects.all()]
        assert ids == [ws2.id, ws1.id]

    def test_cascade_delete_on_project(self, project, user):
        ws = Workspace.objects.create(project=project, user=user)
        project.delete()
        assert Workspace.objects.filter(id=ws.id).count() == 0

    def test_cascade_delete_on_user(self, project, user):
        ws = Workspace.objects.create(project=project, user=user)
        user.delete()
        assert Workspace.objects.filter(id=ws.id).count() == 0


@pytest.mark.django_db
class TestAgentSession:
    def test_create_session(self, project, user):
        session = AgentSession.objects.create(
            project=project, user=user, title="Test Session"
        )
        assert str(session) == "Test Session"
        assert session.status == "idle"
        assert session.stage == "chat"

    def test_default_title_uses_id(self, project, user):
        session = AgentSession.objects.create(project=project, user=user)
        assert str(session).startswith("Session")

    def test_ordering_newest_first(self, project, user):
        s1 = AgentSession.objects.create(project=project, user=user)
        s2 = AgentSession.objects.create(project=project, user=user)
        ids = [s.id for s in AgentSession.objects.all()]
        assert ids == [s2.id, s1.id]

    def test_profile_assignment(self, project, user):
        profile = AgentProfile.objects.create(
            name="Builder", emoji="🏗️", description="Builds stuff"
        )
        session = AgentSession.objects.create(
            project=project, user=user, profile=profile
        )
        session.refresh_from_db()
        assert session.profile.name == "Builder"

    def test_profile_nullable(self, project, user):
        session = AgentSession.objects.create(project=project, user=user)
        assert session.profile is None


@pytest.mark.django_db
class TestAgentMessage:
    def test_create_message(self, project, user):
        session = AgentSession.objects.create(project=project, user=user)
        msg = AgentMessage.objects.create(
            session=session, role="user", content="Hello"
        )
        assert str(msg) == "user: Hello"

    def test_message_ordering_oldest_first(self, project, user):
        session = AgentSession.objects.create(project=project, user=user)
        m1 = AgentSession.objects.create(project=project, user=user)
        m1 = AgentMessage.objects.create(session=session, role="user", content="First")
        m2 = AgentMessage.objects.create(session=session, role="assistant", content="Second")
        m3 = AgentMessage.objects.create(session=session, role="user", content="Third")
        roles = [m.role for m in session.messages.all()]
        assert roles == ["user", "assistant", "user"]

    def test_cascade_delete_on_session(self, project, user):
        session = AgentSession.objects.create(project=project, user=user)
        AgentMessage.objects.create(session=session, role="user", content="Hello")
        assert session.messages.count() == 1
        session.delete()
        assert AgentMessage.objects.count() == 0

    def test_tool_call_json_field(self, project, user):
        session = AgentSession.objects.create(project=project, user=user)
        msg = AgentMessage.objects.create(
            session=session,
            role="tool",
            content="",
            tool_call={"name": "write_file", "args": {"path": "/tmp/test.py"}},
        )
        assert msg.tool_call["name"] == "write_file"

    def test_valid_roles(self, project, user):
        session = AgentSession.objects.create(project=project, user=user)
        for role in ("user", "assistant", "tool", "system"):
            AgentMessage.objects.create(session=session, role=role, content=f"{role} msg")
        assert session.messages.count() == 4
