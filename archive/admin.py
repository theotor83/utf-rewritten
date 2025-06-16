from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.FakeUser)
admin.site.register(models.ArchiveForumGroup)
admin.site.register(models.ArchiveProfile)
admin.site.register(models.ArchiveCategory)
admin.site.register(models.ArchivePost)
admin.site.register(models.ArchiveTopic)
admin.site.register(models.ArchiveForum)
admin.site.register(models.ArchiveTopicReadStatus)
admin.site.register(models.ArchiveSmileyCategory)
admin.site.register(models.ArchivePoll)
admin.site.register(models.ArchivePollOption)
admin.site.register(models.ArchivePollOptionVoters)
admin.site.register(models.ArchiveSubforum)