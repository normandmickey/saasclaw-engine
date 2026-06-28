from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('deployments', '0008_node_ssr'),
    ]

    operations = [
        migrations.AlterField(
            model_name='environment',
            name='runtime_kind',
            field=models.CharField(
                choices=[
                    ('static', 'Static'),
                    ('node_static', 'Node Static'),
                    ('node_ssr', 'Node SSR'),
                    ('django', 'Django'),
                    ('dotnet', '.NET'),
                ],
                default='static',
                max_length=20,
            ),
        ),
    ]
