from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.FakeUser)
admin.site.register(models.ArchiveForumGroup)
#admin.site.register(models.ArchiveProfile)
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

@admin.register(models.ArchiveProfile)
class ArchiveProfileAdmin(admin.ModelAdmin):
    
    def save_model(self, request, obj, form, change):
        # Save the basic model fields first (excluding M2M)
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # Save M2M fields now (including groups)
        super().save_related(request, form, formsets, change)

        # Now M2M fields are saved — we can safely update name_color
        user = form.instance
        top_group = user.get_top_group
        user.name_color = top_group.color if top_group and top_group.color else "#FFFFFF"
        user.save(update_fields=['name_color'])