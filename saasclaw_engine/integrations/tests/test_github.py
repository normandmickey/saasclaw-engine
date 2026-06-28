"""Tests for GitHub integration — clone, push, auth token sanitization."""
from unittest.mock import patch, MagicMock
import subprocess
import pytest
from django.test import TestCase


class TestCloneOrUpdateRepo:
    """Test clone_or_update_repo with mocked subprocess."""

    @patch('saasclaw_engine.integrations.github.time.sleep')
    @patch('saasclaw_engine.integrations.github.create_installation_access_token', return_value='ghs-test-token')
    @patch('saasclaw_engine.integrations.github.subprocess.run')
    def test_successful_clone(self, mock_run, mock_token, mock_sleep):
        mock_run.return_value = None
        from saasclaw_engine.integrations.github import clone_or_update_repo
        dest = clone_or_update_repo(1, 'acme', 'demo', 'main', '/tmp/demo')
        assert dest == '/tmp/demo'

    @patch('saasclaw_engine.integrations.github.time.sleep')
    @patch('saasclaw_engine.integrations.github.create_installation_access_token', return_value='ghs-secret')
    @patch('saasclaw_engine.integrations.github.subprocess.run')
    def test_token_redacted_in_error_message(self, mock_run, mock_token, mock_sleep):
        """Tokens must never appear in error messages."""
        from saasclaw_engine.integrations.github import clone_or_update_repo
        error = subprocess.CalledProcessError(
            128, ['git', 'clone', 'https://x-access-token:ghs-secret@github.com/acme/demo.git', '/tmp/demo'],
            stderr='fatal: repository not found'
        )
        mock_run.side_effect = [error, error, error, error, error, error]
        with pytest.raises(RuntimeError) as exc:
            clone_or_update_repo(1, 'acme', 'demo', 'main', '/tmp/demo')
        msg = str(exc.value)
        assert 'ghs-secret' not in msg
        assert 'Git clone failed' in msg

    @patch('saasclaw_engine.integrations.github.time.sleep')
    @patch('saasclaw_engine.integrations.github.create_installation_access_token', return_value='ghs-secret')
    @patch('saasclaw_engine.integrations.github.subprocess.run')
    def test_retries_on_failure(self, mock_run, mock_token, mock_sleep):
        """Should retry multiple times before giving up."""
        from saasclaw_engine.integrations.github import clone_or_update_repo
        error = subprocess.CalledProcessError(
            128, ['git'], stderr='fatal: not ready'
        )
        mock_run.side_effect = [error, error, error, error, None]
        dest = clone_or_update_repo(1, 'acme', 'demo', 'main', '/tmp/demo')
        assert mock_run.call_count == 5
        assert dest == '/tmp/demo'

    @patch('saasclaw_engine.integrations.github.time.sleep')
    @patch('saasclaw_engine.integrations.github.create_installation_access_token', return_value='ghs-secret')
    @patch('saasclaw_engine.integrations.github.subprocess.run')
    def test_token_not_persisted_in_remote_url(self, mock_run, mock_token, mock_sleep):
        """Token should use auth header, not be baked into the remote URL."""
        from saasclaw_engine.integrations.github import clone_or_update_repo
        ok = subprocess.CompletedProcess(args=['git'], returncode=0, stdout='', stderr='')
        mock_run.side_effect = [ok, ok, ok, ok]
        clone_or_update_repo(1, 'acme', 'demo', 'main', '/tmp/demo')
        # Check that the set-url command does NOT contain the token
        set_url_cmd = mock_run.call_args_list[0].args[0]
        url = str(set_url_cmd)
        assert 'ghs-secret' not in url


class TestCommitAndPush:
    """Test commit_and_push_repo."""

    @patch('saasclaw_engine.integrations.github.create_installation_access_token', return_value='ghs-push-token')
    @patch('saasclaw_engine.integrations.github.subprocess.run')
    def test_uses_auth_header(self, mock_run, mock_token):
        """Token should be in auth header, not in the URL."""
        from saasclaw_engine.integrations.github import commit_and_push_repo
        ok = subprocess.CompletedProcess(args=['git'], returncode=0, stdout='', stderr='')
        mock_run.side_effect = [ok, ok, ok, ok, ok, ok, ok, ok]
        commit_and_push_repo(1, 'acme', 'demo', 'main', '/tmp/demo', 'test commit')
        # Last two calls: set-url and push
        set_url_cmd = mock_run.call_args_list[-2].args[0]
        assert 'ghs-push-token' not in str(set_url_cmd)
