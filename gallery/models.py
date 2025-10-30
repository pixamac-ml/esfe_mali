from django.db import models

class Album(models.Model):
    title = models.CharField("Titre", max_length=200)
    description = models.TextField("Description", blank=True)
    cover = models.ImageField("Image de couverture", upload_to="gallery/covers/")
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Album"
        verbose_name_plural = "Albums"

    def __str__(self):
        return self.title


class Media(models.Model):
    IMAGE = "image"
    VIDEO = "video"
    TYPE_CHOICES = [
        (IMAGE, "Image"),
        (VIDEO, "Vidéo"),
    ]

    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="media", verbose_name="Album")
    type = models.CharField("Type", max_length=10, choices=TYPE_CHOICES, default=IMAGE)
    file = models.FileField("Fichier", upload_to="gallery/media/", blank=True, null=True)
    url = models.URLField("URL (YouTube/Vimeo)", blank=True, null=True)
    caption = models.CharField("Légende", max_length=200, blank=True)
    uploaded_at = models.DateTimeField("Ajouté le", auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Média"
        verbose_name_plural = "Médias"

    def __str__(self):
        return f"{self.type} - {self.album.title}"
