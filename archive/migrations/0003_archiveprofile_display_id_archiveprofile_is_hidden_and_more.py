# Generated by Django 5.1.6 on 2025-06-15 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive', '0002_populate_database'),
        ('precise_bbcode', '0002_alter_bbcodetag_id_alter_smileytag_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='archiveprofile',
            name='display_id',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='archiveprofile',
            name='is_hidden',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='archivetopic',
            name='display_children',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='archivetopic',
            name='display_id',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='archivetopic',
            name='display_replies',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='archivetopic',
            name='display_views',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='archiveprofile',
            name='profile_picture',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='archivesmileycategory',
            name='smileys',
            field=models.ManyToManyField(blank=True, related_name='archive_categories', to='precise_bbcode.smileytag'),
        ),
        migrations.DeleteModel(
            name='ArchiveSmileyCategory_smileys',
        ),
    ]
