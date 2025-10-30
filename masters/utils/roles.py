# masters/utils/roles.py

def user_role(user):
    """
    Retourne le rôle simplifié (student | instructor | staff_admin)
    Compatible avec ton modèle CustomUser.role et les Groupes Django.
    """
    if not user.is_authenticated:
        return None

    # 1️⃣ Priorité au champ 'role' (CustomUser)
    if hasattr(user, "role") and user.role:
        role_value = str(user.role).upper().strip()
        role_map = {
            "DIRECTEUR": "staff_admin",
            "GESTIONNAIRE": "staff_admin",
            "SECRETAIRE": "staff_admin",
            "ADMIN": "staff_admin",
            "AGENT_MARKETING": "staff_admin",
            "ENSEIGNANT": "instructor",
            "ETUDIANT": "student",
        }
        return role_map.get(role_value, "student")

    # 2️⃣ Fallback via les groupes Django (si role non défini)
    names = {g.name.lower() for g in user.groups.all()}

    # Staff administratif
    if names & {
        "directeur", "conseiller", "informaticien", "secretaire",
        "gestionnaire", "administrateurs", "admin", "direction"
    }:
        return "staff_admin"

    # Enseignant
    if names & {"enseignant", "enseignants", "teacher", "instructor"}:
        return "instructor"

    # Étudiant
    if names & {"etudiant", "etudiants", "students", "student"}:
        return "student"

    # Par défaut
    return "student"


# Helpers pratiques
def is_student(user):
    return user_role(user) == "student"

def is_instructor(user):
    return user_role(user) == "instructor"

def is_staff_admin(user):
    return user_role(user) == "staff_admin"
