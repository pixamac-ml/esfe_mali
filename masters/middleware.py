# masters/middleware.py
from django.shortcuts import redirect
from django.urls import resolve, reverse
from .utils.roles import user_role  # ✅ on utilise la fonction unifiée


class MasterAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        path = request.path.lower()

        # =======================================================
        # 0️⃣ LAISSER PASSER LES ROUTES PUBLIQUES ET INTERNES SPÉCIALES
        # =======================================================
        if (
            path.startswith("/masters/messenger/") or  # 🟢 App Messenger intégrée
            path.startswith("/ws/") or                 # 🟢 WebSockets (Channels)
            path.startswith("/admin/") or              # 🟢 Admin Django
            path.startswith("/static/") or             # 🟢 Fichiers statiques
            path.startswith("/media/")                 # 🟢 Fichiers médias (ex: enregistrements)
        ):
            return self.get_response(request)

        # =======================================================
        # 1️⃣ OBLIGATION DE CHANGEMENT DE MOT DE PASSE
        # =======================================================
        if (
            user.is_authenticated
            and hasattr(user, "userprofile")
            and getattr(user.userprofile, "must_change_password", False)
            and not request.path.startswith(reverse("masters:force_password_change"))
            and not request.path.startswith("/admin")
        ):
            return redirect("masters:force_password_change")

        # =======================================================
        # 2️⃣ REDIRECTION AUTO À L’ENTRÉE DU PORTAIL MASTER
        # =======================================================
        try:
            if user.is_authenticated and resolve(request.path_info).url_name == "portal":
                role = user_role(user)
                if role == "student":
                    return redirect("masters:student_dashboard")
                elif role == "instructor":
                    return redirect("masters:dashboard")
                elif role == "staff_admin":
                    return redirect("masters:dashboard")
        except Exception:
            pass

        # =======================================================
        # 3️⃣ PROTECTION DES ROUTES SELON LE RÔLE
        # =======================================================
        if user.is_authenticated:
            role = user_role(user)

            # Étudiant : accès uniquement à son espace
            if role == "student" and (
                "/teacher/" in path or "/manage/" in path or "/finance/" in path
            ):
                return redirect("masters:student_dashboard")

            # Enseignant : pas d’accès aux zones staff
            if role == "instructor" and (
                "/manage/" in path or "/finance/" in path or "/staff/" in path
            ):
                return redirect("masters:dashboard")

            # Staff : pas d’accès aux zones étudiants ou enseignants
            if role == "staff_admin" and (
                "/student/" in path or "/teacher/" in path
            ):
                return redirect("masters:dashboard")

        # =======================================================
        # 4️⃣ CONTINUER LA CHAÎNE DE MIDDLEWARES
        # =======================================================
        return self.get_response(request)
