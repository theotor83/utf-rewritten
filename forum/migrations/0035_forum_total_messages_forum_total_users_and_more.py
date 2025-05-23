# Generated by Django 5.1.6 on 2025-03-06 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0034_topicreadstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='forum',
            name='total_messages',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='forum',
            name='total_users',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='topic',
            name='total_replies',
            field=models.IntegerField(default=-1),
        ),
    ]
