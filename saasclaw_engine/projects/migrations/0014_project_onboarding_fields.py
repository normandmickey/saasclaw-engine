from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0013_project_support_widget_button_label_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='onboarding_completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='onboarding_goal_prompt',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='onboarding_step',
            field=models.CharField(blank=True, choices=[('start', 'Start'), ('github', 'GitHub'), ('generate', 'Generate'), ('building', 'Building'), ('widgets', 'Widgets'), ('ready', 'Ready'), ('done', 'Done')], default='start', max_length=32),
        ),
    ]
