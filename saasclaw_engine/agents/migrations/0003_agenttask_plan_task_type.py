from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0002_agenttask_parent_task_agenttask_thread_key_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agenttask',
            name='task_type',
            field=models.CharField(
                choices=[
                    ('plan', 'Plan'),
                    ('edit_code', 'Edit Code'),
                    ('generate_site', 'Generate Site'),
                    ('fix_bug', 'Fix Bug'),
                    ('inspect_repo', 'Inspect Repo'),
                    ('deploy_preview', 'Deploy Preview'),
                    ('deploy_production', 'Deploy Production'),
                ],
                max_length=32,
            ),
        ),
    ]
