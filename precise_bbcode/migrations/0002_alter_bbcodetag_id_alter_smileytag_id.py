# Generated by Django 5.1.6 on 2025-03-01 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('precise_bbcode', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bbcodetag',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='smileytag',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
