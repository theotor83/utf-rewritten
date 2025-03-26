from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.Profile)
admin.site.register(models.ForumGroup)
admin.site.register(models.Post)
admin.site.register(models.Topic)
admin.site.register(models.Category)
admin.site.register(models.Forum)
admin.site.register(models.TopicReadStatus)

