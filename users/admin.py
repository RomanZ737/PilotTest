from django.contrib import admin
from .models import Profile, UserTests, GroupsDescription, TestExpired

admin.site.register(Profile)
admin.site.register(UserTests)
admin.site.register(GroupsDescription)
admin.site.register(TestExpired)
