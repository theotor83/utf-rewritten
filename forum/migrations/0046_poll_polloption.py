# Generated by Django 5.1.6 on 2025-05-15 21:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0045_smileycategory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('max_choices_per_user', models.IntegerField(default=1)),
                ('days_to_vote', models.IntegerField(default=-1)),
                ('topic', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='poll', to='forum.topic', verbose_name='Topic Poll')),
            ],
            options={
                'verbose_name': 'Poll',
                'verbose_name_plural': 'Polls',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PollOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255, verbose_name='Option Text')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='forum.poll')),
                ('voters', models.ManyToManyField(blank=True, related_name='poll_votes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['id'],
                'unique_together': {('poll', 'text')},
            },
        ),
    ]
