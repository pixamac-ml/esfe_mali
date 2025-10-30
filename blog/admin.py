from django.contrib import admin, messages
from django.utils import timezone
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Category, Tag, Post, Comment, Reaction


# ---- FORM ----
class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = "__all__"
        widgets = {
            "content": CKEditor5Widget(config_name="default"),
        }


# ---- ACTIONS ----
@admin.action(description="Publier les articles sélectionnés")
def publish_now(modeladmin, request, queryset):
    updated = queryset.update(status=Post.PUBLISHED, published_at=timezone.now())
    messages.success(request, f"{updated} article(s) publié(s).")


@admin.action(description="Marquer en brouillon")
def mark_draft(modeladmin, request, queryset):
    updated = queryset.update(status=Post.DRAFT)
    messages.info(request, f"{updated} article(s) remis en brouillon.")


@admin.action(description="Approuver les commentaires sélectionnés")
def approve_comments(modeladmin, request, queryset):
    updated = queryset.update(is_approved=True)
    messages.success(request, f"{updated} commentaire(s) approuvé(s).")


# ---- INLINE ----
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("display_name", "message", "is_approved", "is_staff_note", "created_at")
    readonly_fields = ("created_at",)


# ---- POST ----
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ("title", "category", "status", "is_pinned", "published_at", "author")
    list_filter = ("status", "category", "tags", "is_pinned")
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CommentInline]
    actions = [publish_now, mark_draft]


# ---- CATEGORY ----
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


# ---- TAG ----
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


# ---- COMMENT ----
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "display_name", "is_approved", "is_staff_note", "created_at")
    list_filter = ("is_approved", "is_staff_note")
    search_fields = ("message", "display_name")
    actions = [approve_comments]


# ---- REACTION ----
@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "guest_fingerprint", "value", "created_at")
    list_filter = ("value",)
    readonly_fields = ("post", "user", "guest_fingerprint", "value", "created_at")
