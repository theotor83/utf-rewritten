# Generated by Django 5.1.6 on 2025-03-01 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0018_alter_category_index_topics'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='index_topics',
        ),
        migrations.AddField(
            model_name='category',
            name='index_topics',
            field=models.ManyToManyField(blank=True, null=True, related_name='index_topics', to='forum.topic'),
        ),
    ]
