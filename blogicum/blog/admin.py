from django.contrib import admin

from .models import Category, Location, Post, Comment

admin.site.register([Category, Location, Post, Comment])
