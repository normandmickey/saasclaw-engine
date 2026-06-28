from django.conf import settings
from django.db import models


class GitHubInstallation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='github_installations', null=True, blank=True)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50, blank=True)
    installation_id = models.BigIntegerField(unique=True)
    github_account_id = models.BigIntegerField(null=True, blank=True)
    access_metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['account_name', 'installation_id']

    def __str__(self):
        return f'{self.account_name} ({self.installation_id})'
