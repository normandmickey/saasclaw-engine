from django.contrib import admin

from .models import AgentTask


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    list_display = ('project', 'task_type', 'status', 'requested_by', 'linked_branch', 'linked_commit_sha', 'created_at')
    list_filter = ('task_type', 'status')
    search_fields = ('project__name', 'project__slug', 'requested_by__username', 'requested_by__email', 'linked_branch', 'linked_commit_sha')
    readonly_fields = ('created_at', 'started_at', 'finished_at')
