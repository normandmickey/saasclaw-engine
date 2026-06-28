from django.contrib import admin

from .models import GitHubInstallation


@admin.register(GitHubInstallation)
class GitHubInstallationAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'installation_id', 'github_account_id', 'user', 'updated_at')
    search_fields = ('account_name', 'installation_id', 'github_account_id', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
