from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Application, Job, RelevanceRating, Resume, User, WeightConfig

admin.site.register(User, UserAdmin)
admin.site.register([Job, Resume, Application, WeightConfig, RelevanceRating])
