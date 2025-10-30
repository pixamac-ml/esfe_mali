from django.contrib import admin
from .models import News, NewsMedia

class NewsMediaInline(admin.TabularInline):
    model = NewsMedia
    extra = 1

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "published_at", "author")
    list_filter = ("type", "published_at")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [NewsMediaInline]

@admin.register(NewsMedia)
class NewsMediaAdmin(admin.ModelAdmin):
    list_display = ("news", "type", "caption")
    list_filter = ("type",)
