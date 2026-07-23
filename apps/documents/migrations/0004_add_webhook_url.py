from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_add_bilingual'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentjob',
            name='webhook_url',
            field=models.URLField(blank=True, default=''),
        ),
    ]
