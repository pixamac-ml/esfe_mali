from django.contrib.auth import get_user_model

User = get_user_model()


def is_ajax(request):
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.GET.get("fragment") == "1"
    )


def user_queryset_for_messenger(current_user):
    """
    Retourne les utilisateurs qu'on peut lister dans "Nouvelle conversation".
    On enlève juste l'utilisateur courant.
    """
    return User.objects.exclude(id=current_user.id).order_by("first_name", "last_name", "username")
