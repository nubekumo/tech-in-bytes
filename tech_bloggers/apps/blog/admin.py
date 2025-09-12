from django.contrib import admin
from .models import Post, Tag, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "published_at")
    list_filter = ("status", "tags", "published_at")
    search_fields = ("title", "author", "content")
    prepopulated_fields = {"slug": ("title",)}  # if you add a slug field
    date_hierarchy = "published_at"
    ordering = ("-published_at",)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "created_at", "active")
    list_filter = ("active", "created_at")
    search_fields = ("author__username", "text")

