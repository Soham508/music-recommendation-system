from django.contrib import admin
from .models import User, Song, UserActivity # Import your models here

# Register your models here
admin.site.register(User)
admin.site.register(Song)
admin.site.register(UserActivity)