# Generated by Django 5.1.6 on 2025-03-01 23:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0024_alter_topic_last_message_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='Forum',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('announcement_topics', models.ManyToManyField(to='forum.topic')),
            ],
        ),
    ]
