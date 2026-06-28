from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'framework', 'owner', 'last_deployed_at')
    list_filter = ('status', 'framework')
    search_fields = ('name', 'slug', 'repo_url')
    readonly_fields = ('created_at', 'updated_at')
