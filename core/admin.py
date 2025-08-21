from django.contrib import admin
from .models import SiteSettings, SocialLink, Menu, MenuItem, SimplePage, HomeHero, SiteAnnouncement, RedirectRule

class SocialInline(admin.TabularInline):
    model = SocialLink
    extra = 1

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    inlines = [SocialInline]
    fieldsets = (
        ("Identité", {"fields": ("site_name", "tagline", "logo", "favicon")}),
        ("Contacts", {"fields": ("email","phone_main","whatsapp","address","map_embed")}),
        ("Intégrations", {"fields": ("ga4_id","meta_pixel_id")}),
        ("SEO défaut", {"fields": ("meta_title","meta_description","og_image")}),
    )

class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 2

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("title","location","slug")
    inlines = [MenuItemInline]

@admin.register(SimplePage)
class SimplePageAdmin(admin.ModelAdmin):
    list_display = ("title","slug","is_published","updated_at")
    list_filter = ("is_published",)
    search_fields = ("title","slug","body")

@admin.register(HomeHero)
class HomeHeroAdmin(admin.ModelAdmin):
    list_display = ("headline","is_active","order")
    list_editable = ("is_active","order")

@admin.register(SiteAnnouncement)
class SiteAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("message","level","is_active","starts_at","ends_at")
    list_filter = ("level","is_active")

@admin.register(RedirectRule)
class RedirectAdmin(admin.ModelAdmin):
    list_display = ("old_path","new_path","permanent","active")
    list_filter = ("permanent","active")
