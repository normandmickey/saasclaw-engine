from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0027_project_require_gateway'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Proposed project name', max_length=128)),
                ('slug', models.SlugField(help_text='URL-safe project slug', max_length=128)),
                ('description', models.TextField(blank=True, help_text='What the project does, goals, audience')),
                ('framework', models.CharField(default='html', help_text='Desired framework/template', max_length=64)),
                ('source', models.CharField(default='blank', help_text='blank, template, or github', max_length=64)),
                ('template', models.CharField(blank=True, help_text='Template name if applicable', max_length=64)),
                ('repo_url', models.URLField(blank=True, help_text='GitHub URL if importing')),
                ('business_justification', models.TextField(blank=True, help_text='Why this project is needed, who will use it, compliance requirements')),
                ('data_sensitivity', models.CharField(blank=True, default='', help_text='Data sensitivity level: none, low, medium, high (PII/PHI)', max_length=64)),
                ('estimated_timeline', models.CharField(blank=True, max_length=128, help_text='When they need it, urgency level')),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='pending', max_length=32)),
                ('staff_notes', models.TextField(blank=True, help_text='Internal staff notes')),
                ('require_gateway', models.BooleanField(default=False, help_text='Staff can pre-set gateway requirement on approval')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_submissions', to=settings.AUTH_USER_MODEL)),
                ('reviewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_submissions', to=settings.AUTH_USER_MODEL)),
                ('approved_project', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submission', to='projects.project')),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Project Submission',
            },
        ),
    ]
