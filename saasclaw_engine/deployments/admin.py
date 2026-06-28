from django.contrib import admin

from .models import Deployment, Environment, EnvironmentVariable


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('project', 'name', 'domain', 'runtime_kind', 'is_primary', 'updated_at')
    list_filter = ('name', 'runtime_kind', 'is_primary')
    search_fields = ('project__name', 'project__slug', 'domain')


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ('project', 'environment', 'status', 'source', 'git_branch', 'git_commit_sha', 'created_at')
    list_filter = ('status', 'source', 'environment__name')
    search_fields = ('project__name', 'project__slug', 'git_branch', 'git_commit_sha')
    readonly_fields = ('created_at', 'started_at', 'finished_at')


@admin.register(EnvironmentVariable)
class EnvironmentVariableAdmin(admin.ModelAdmin):
    list_display = ('key', 'project', 'environment', 'is_secret', 'updated_at')
    list_filter = ('environment__name', 'is_secret')
    search_fields = ('key', 'project__name', 'project__slug')
    fields = ('project', 'environment', 'key', 'value', 'is_secret')
