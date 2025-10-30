# masters/apps.py
from django.apps import AppConfig

class MastersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'masters'

    def ready(self):
        import masters.signals
        import admissions.signals   # ✅ assure que les signaux d’admission sont toujours chargés
