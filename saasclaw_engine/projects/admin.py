from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'framework', 'owner', 'last_deployed_at')
    list_filter = ('status', 'framework')
    search_fields = ('name', 'slug', 'repo_url')
    readonly_fields = ('created_at', 'updated_at')

from django.contrib import admin
from .models import ProjectSubmission


@admin.register(ProjectSubmission)
class ProjectSubmissionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "requester", "status", "data_sensitivity", "created_at")
    list_filter = ("status", "data_sensitivity", "created_at")
    search_fields = ("name", "slug", "requester__username", "description")
    readonly_fields = ("requester", "created_at", "updated_at")
    fieldsets = (
        ("Request", {
            "fields": ("requester", "name", "slug", "description", "framework", "source", "template", "repo_url")
        }),
        ("Context", {
            "fields": ("business_justification", "data_sensitivity", "estimated_timeline")
        }),
        ("Review", {
            "fields": ("status", "reviewer", "staff_notes", "require_gateway", "reviewed_at", "approved_project")
        }),
    )
