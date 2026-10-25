from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Application, Job, Resume, User

admin.site.register(User, UserAdmin)
admin.site.register([Job, Resume, Application])
