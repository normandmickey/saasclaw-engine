"""Tests for AgentTask management."""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class TestAgentTask:
    """Tests for the agent task model and state management."""

    @pytest.mark.django_db
    def test_task_creation(self):
        from saasclaw_engine.agents.models import AgentTask
        from saasclaw_engine.projects.models import Project
        user = User.objects.create_user(username='agent_test', password='***')
        project = Project.objects.create(
            owner=user, name='Task Test', slug='task-test', framework='html'
        )
        task = AgentTask.objects.create(
            project=project,
            requested_by=user,
            task_type='edit_code',
            prompt='Build a todo app',
        )
        assert task.prompt == 'Build a todo app'
        assert task.status == 'queued'
        assert task.task_type == 'edit_code'

    @pytest.mark.django_db
    def test_task_status_lifecycle(self):
        from saasclaw_engine.agents.models import AgentTask
        from saasclaw_engine.projects.models import Project
        user = User.objects.create_user(username='lifecycle_test', password='***')
        project = Project.objects.create(
            owner=user, name='Lifecycle', slug='lifecycle', framework='html'
        )
        task = AgentTask.objects.create(
            project=project,
            requested_by=user,
            task_type='fix_bug',
            prompt='Fix the CSS bug',
        )
        assert task.status == 'queued'
        task.status = 'running'
        task.save()
        task.status = 'succeeded'
        task.save()
        assert task.status == 'succeeded'

    @pytest.mark.django_db
    def test_task_type_choices(self):
        """All declared task types should be valid."""
        from saasclaw_engine.agents.models import AgentTask
        valid_types = [c[0] for c in AgentTask.TaskType.choices]
        expected = ['plan', 'edit_code', 'create_resource', 'generate_site',
                    'fix_bug', 'inspect_repo', 'deploy_preview', 'deploy_production']
        for t in expected:
            assert t in valid_types, f"Missing task type: {t}"

    @pytest.mark.django_db
    def test_task_scoped_to_project(self):
        from saasclaw_engine.agents.models import AgentTask
        from saasclaw_engine.projects.models import Project
        user = User.objects.create_user(username='scope_test', password='***')
        p1 = Project.objects.create(owner=user, name='P1', slug='scope-p1', framework='html')
        p2 = Project.objects.create(owner=user, name='P2', slug='scope-p2', framework='html')
        AgentTask.objects.create(project=p1, requested_by=user, task_type='plan', prompt='Plan 1')
        AgentTask.objects.create(project=p2, requested_by=user, task_type='plan', prompt='Plan 2')
        assert p1.agent_tasks.count() == 1
        assert p2.agent_tasks.count() == 1

    @pytest.mark.django_db
    def test_task_error_message(self):
        from saasclaw_engine.agents.models import AgentTask
        from saasclaw_engine.projects.models import Project
        user = User.objects.create_user(username='error_test', password='***')
        project = Project.objects.create(
            owner=user, name='Error Test', slug='error-test', framework='html'
        )
        task = AgentTask.objects.create(
            project=project,
            requested_by=user,
            task_type='fix_bug',
            prompt='Fix something',
            status='failed',
            error_message='Command failed: exit 1',
        )
        task.save()
        assert task.error_message == 'Command failed: exit 1'
