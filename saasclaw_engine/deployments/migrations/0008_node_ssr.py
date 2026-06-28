from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('deployments', '0007_merge_0002_environmentvariable_0006_customdomain'),
    ]

    operations = [
        migrations.AlterField(
            model_name='environment',
            name='runtime_kind',
            field=models.CharField(
                choices=[('static', 'Static'), ('node_static', 'Node Static'), ('node_ssr', 'Node SSR'), ('django', 'Django')],
                default='static',
                max_length=20,
            ),
        ),
    ]
