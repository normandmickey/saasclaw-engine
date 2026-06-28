"""Add EnvironmentVariable model."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0005_alter_deployment_deploy_log_object_key_and_more'),
        ('projects', '0022_remove_aiactionrequest_requested_by_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnvironmentVariable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=255)),
                ('value', models.TextField(blank=True)),
                ('is_secret', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variables', to='deployments.environment')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='env_variables', to='projects.project')),
            ],
            options={
                'unique_together': {('environment', 'key')},
                'ordering': ['key'],
            },
        ),
    ]
