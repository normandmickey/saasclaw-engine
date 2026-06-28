from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_resourcedefinition_resourcefielddefinition'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='chat_widget_api_key',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='chat_widget_button_label',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='project',
            name='chat_widget_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='project',
            name='chat_widget_model',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='project',
            name='chat_widget_provider',
            field=models.CharField(choices=[('openai', 'OpenAI'), ('anthropic', 'Anthropic'), ('gemini', 'Google Gemini')], default='openai', max_length=20),
        ),
        migrations.AddField(
            model_name='project',
            name='chat_widget_system_prompt',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='chat_widget_title',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='project',
            name='chat_widget_welcome_message',
            field=models.TextField(blank=True),
        ),
    ]
