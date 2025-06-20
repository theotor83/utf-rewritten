# Generated by Django 5.1.6 on 2025-06-20 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='archiveprofile',
            name='gender',
            field=models.CharField(choices=[('male', 'Masculin'), ('female', 'Féminin')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='archiveprofile',
            name='type',
            field=models.CharField(choices=[('pacifist', 'Pacifiste'), ('neutral', 'Neutre'), ('genocide', 'Génocidaire')], default='neutral', max_length=20, null=True),
        ),
    ]
