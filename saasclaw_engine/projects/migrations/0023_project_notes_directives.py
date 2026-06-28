from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0022_remove_aiactionrequest_requested_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='notes',
            field=models.TextField(blank=True, help_text='Project notes and context'),
        ),
        migrations.AddField(
            model_name='project',
            name='directives',
            field=models.TextField(blank=True, help_text='Standing instructions for the agent'),
        ),
    ]
