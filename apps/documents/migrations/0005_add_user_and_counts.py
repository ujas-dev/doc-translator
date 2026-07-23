from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0004_add_webhook_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentjob',
            name='user',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='document_jobs',
            ),
        ),
        migrations.AddField(
            model_name='documentjob',
            name='page_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='documentjob',
            name='character_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='documentjob',
            options={'ordering': ['-created_at']},
        ),
    ]
