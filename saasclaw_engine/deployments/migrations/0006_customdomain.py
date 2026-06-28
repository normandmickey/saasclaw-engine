from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0005_alter_deployment_deploy_log_object_key_and_more'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomDomain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=255, unique=True)),
                ('status', models.CharField(choices=[('pending_dns', 'Pending DNS'), ('verifying', 'Verifying'), ('ssl_requesting', 'Requesting SSL'), ('active', 'Active'), ('failed', 'Failed')], default='pending_dns', max_length=20)),
                ('dns_verified_at', models.DateTimeField(blank=True, null=True)),
                ('ssl_cert_path', models.CharField(blank=True, max_length=500)),
                ('ssl_key_path', models.CharField(blank=True, max_length=500)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_domains', to='projects.project')),
            ],
        ),
    ]
