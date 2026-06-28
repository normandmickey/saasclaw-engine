from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0007_project_chat_widget_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='default_ai_api_key',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='default_ai_model',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='project',
            name='default_ai_provider',
            field=models.CharField(choices=[('openai', 'OpenAI'), ('anthropic', 'Anthropic'), ('gemini', 'Google Gemini')], default='openai', max_length=20),
        ),
        migrations.AddField(
            model_name='project',
            name='default_ai_system_prompt',
            field=models.TextField(blank=True),
        ),
    ]
