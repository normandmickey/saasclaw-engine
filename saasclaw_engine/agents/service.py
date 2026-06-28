"""Agent service — stripped to deploy-only.

The AI edit / scaffold / code generation logic has been removed.
The studio app will handle code editing in a future phase.
"""
from .models import AgentTask


def run_ai_edit_task(task: AgentTask, *, auto_deploy_preview: bool = False) -> None:
    """Placeholder — studio app will implement agent-driven code editing."""
    task.status = AgentTask.Status.FAILED
    task.error_message = 'AI edit tasks are not available until the studio app is built.'
    task.save(update_fields=['status', 'error_message'])
