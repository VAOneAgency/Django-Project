from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publisher', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('instagram', 'Instagram'), ('facebook', 'Facebook')], default='instagram', max_length=20)),
                ('object_type', models.CharField(blank=True, help_text="e.g. 'instagram', 'page'", max_length=100)),
                ('entry_id', models.CharField(blank=True, help_text='ID of the object that triggered the event', max_length=255)),
                ('field', models.CharField(blank=True, help_text="Webhook field subscribed to, e.g. 'comments', 'messages'", max_length=100)),
                ('raw_payload', models.TextField(help_text='Full JSON payload from Meta')),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('processed', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'tblwebhook_events',
                'ordering': ['-received_at'],
            },
        ),
    ]
