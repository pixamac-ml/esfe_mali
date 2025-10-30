from django.contrib import admin
from .models import Album, Media

class MediaInline(admin.TabularInline):
    model = Media
    extra = 2
    fields = ("type", "file", "url", "caption")

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title", "description")
    inlines = [MediaInline]

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ("album", "type", "caption", "uploaded_at")
    list_filter = ("type", "uploaded_at")
    search_fields = ("caption",)
