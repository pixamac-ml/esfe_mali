from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

User = settings.AUTH_USER_MODEL

class News(models.Model):
    EVENT = "event"
    ANNOUNCEMENT = "announcement"
    GENERAL = "general"
    TYPE_CHOICES = [
        (EVENT, "Événement"),
        (ANNOUNCEMENT, "Annonce"),
        (GENERAL, "Actualité générale"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=GENERAL)

    cover = models.ImageField(upload_to="news/covers/", blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("news:detail", args=[self.slug])

    def __str__(self):
        return self.title


class NewsMedia(models.Model):
    IMAGE = "image"
    VIDEO = "video"
    TYPE_CHOICES = [
        (IMAGE, "Image"),
        (VIDEO, "Vidéo"),
    ]

    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="media")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file = models.FileField(upload_to="news/media/", blank=True, null=True)
    url = models.URLField(blank=True, null=True, help_text="Lien YouTube/Vimeo pour les vidéos externes")
    caption = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.type} → {self.news.title}"
