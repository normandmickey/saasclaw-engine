from django.db import migrations, models
import secrets


def populate_ai_gateway_tokens(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    for project in Project.objects.all().only('id', 'ai_gateway_token'):
        if not project.ai_gateway_token:
            project.ai_gateway_token = secrets.token_urlsafe(32)
            project.save(update_fields=['ai_gateway_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0014_project_onboarding_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='ai_gateway_token',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.RunPython(populate_ai_gateway_tokens, migrations.RunPython.noop),
    ]
