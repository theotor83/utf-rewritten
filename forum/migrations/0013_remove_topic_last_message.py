# Generated by Django 5.1.6 on 2025-02-27 18:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0012_rename_post_post_topic'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topic',
            name='last_message',
        ),
    ]
