from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0016_tenant_copilotsession_aiactionrequest_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InboundMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(choices=[('manual', 'Manual'), ('forwarded', 'Forwarded'), ('email_sync', 'Email sync')], default='manual', max_length=20)),
                ('external_message_id', models.CharField(blank=True, max_length=255)),
                ('sender_name', models.CharField(blank=True, max_length=255)),
                ('sender_email', models.EmailField(blank=True, max_length=254)),
                ('to_emails_json', models.JSONField(blank=True, default=list)),
                ('cc_emails_json', models.JSONField(blank=True, default=list)),
                ('subject', models.CharField(max_length=255)),
                ('body_text', models.TextField(blank=True)),
                ('body_html', models.TextField(blank=True)),
                ('received_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('new', 'New'), ('processed', 'Processed'), ('needs_review', 'Needs review'), ('ready_to_apply', 'Ready to apply'), ('applied', 'Applied'), ('closed', 'Closed')], default='new', max_length=20)),
                ('routing_confidence', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('routing_reason', models.TextField(blank=True)),
                ('intent', models.CharField(choices=[('create_record', 'Create record'), ('update_record', 'Update record'), ('attach_artifact', 'Attach artifact'), ('draft_reply', 'Draft reply'), ('ambiguous', 'Ambiguous')], default='ambiguous', max_length=30)),
                ('parsed_json', models.JSONField(blank=True, default=dict)),
                ('reply_draft', models.TextField(blank=True)),
                ('applied_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_tenant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inbound_messages', to='projects.tenant')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_inbound_messages', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inbound_messages', to='projects.project')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_inbound_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-received_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='InboundAgentRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('succeeded', 'Succeeded'), ('failed', 'Failed'), ('needs_review', 'Needs review')], default='succeeded', max_length=20)),
                ('confidence', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('decision_json', models.JSONField(blank=True, default=dict)),
                ('proposed_changes_json', models.JSONField(blank=True, default=list)),
                ('error_text', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_runs', to='projects.inboundmessage')),
                ('tenant_guess', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inbound_agent_runs', to='projects.tenant')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InboundAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(max_length=255)),
                ('mime_type', models.CharField(blank=True, max_length=120)),
                ('storage_path', models.CharField(blank=True, max_length=500)),
                ('artifact_type_guess', models.CharField(blank=True, max_length=80)),
                ('extracted_text', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('linked_record', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inbound_attachments', to='projects.tenantrecord')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='projects.inboundmessage')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
