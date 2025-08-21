# core/context_processors.py
from .models import SiteSettings, Menu, SiteAnnouncement

def site_basics(request):
    settings = SiteSettings.objects.first()
    header_menu = Menu.objects.filter(location="header").first()
    footer_menu = Menu.objects.filter(location="footer").first()

    # annonce active (si définie)
    ann = None
    for a in SiteAnnouncement.objects.all():
        if a.active_now():
            ann = a
            break

    return {
        "SITE": settings,
        "HEADER_MENU": header_menu,
        "FOOTER_MENU": footer_menu,
        "SITE_ANNOUNCEMENT": ann,
    }
