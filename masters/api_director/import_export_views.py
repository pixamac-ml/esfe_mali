# masters/api_director/import_export_views.py
"""
API Import–Export pour le Directeur des Études.
- Import de données (Excel, CSV, JSON)
- Export de données (Excel, CSV, PDF, Word, PPTX)
Basé sur utils.import_export_tools
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.http import HttpResponse
from masters.utils.import_export_tools import ImportExportManager
from programs.models import Program
from masters.models import (
    MasterEnrollment, InstructorAssignment, ModuleUE, Exam, SemesterResult,
)
import traceback


# ----------------------------------------------------------
# 🔒 Vérification rôle Directeur
# ----------------------------------------------------------
def is_director(user):
    if not user.is_authenticated:
        return False
    role = (getattr(user, "role", "") or "").upper().strip()
    if role in {"DIRECTEUR_ETUDES", "DIRECTEUR D'ÉTUDES", "DIRECTEUR DES ETUDES", "DIRECTEUR"}:
        return True
    names = {g.name.lower() for g in user.groups.all()}
    return "directeur" in names or "staff_admin" in names


# ==========================================================
# 📥 1️⃣ Importer un fichier (Excel / CSV / JSON)
# ==========================================================
class DirectorImportAPI(APIView):
    """
    Endpoint : POST /api/director/import/
    Corps : form-data => { file, file_type, model_name }
    Ex :
      - file_type = "excel" | "csv" | "json"
      - model_name = "masters.MasterEnrollment"
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_director(request.user):
            return Response({"error": "⛔ Accès réservé au Directeur des Études."}, status=403)

        file = request.FILES.get("file")
        file_type = request.data.get("file_type", "excel").lower()
        model_name = request.data.get("model_name")

        if not file or not model_name:
            return Response(
                {"error": "Paramètres manquants : file et model_name sont requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = ImportExportManager.import_data(model_name, file, file_type)
            return Response(result, status=status.HTTP_200_OK if result.get("ok") else 400)
        except Exception as e:
            return Response(
                {"ok": False, "error": str(e), "trace": traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==========================================================
# 📤 2️⃣ Exporter un fichier (Excel / CSV / PDF / Word / PPTX)
# ==========================================================
class DirectorExportAPI(APIView):
    """
    Endpoint : GET /api/director/export/<format>/?model=<model>&filters=...
    Exemple :
      /api/director/export/excel/?model=masters.MasterEnrollment
      /api/director/export/pdf/?model=masters.Exam&program=2
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, format: str):
        if not is_director(request.user):
            return Response({"error": "⛔ Accès réservé au Directeur des Études."}, status=403)

        model_name = request.GET.get("model")
        if not model_name:
            return Response({"error": "Paramètre 'model' manquant."}, status=400)

        try:
            # Récupère le modèle dynamiquement
            from django.apps import apps
            model = apps.get_model(model_name)
        except Exception as e:
            return Response({"error": f"Modèle introuvable : {e}"}, status=400)

        # Récupération de queryset selon le modèle
        qs = model.objects.all()

        # Filtres simples (si applicable)
        filters = {k: v for k, v in request.GET.items() if k not in {"model", "format"}}
        if filters:
            qs = qs.filter(**filters)

        if not qs.exists():
            return Response({"error": "Aucune donnée à exporter."}, status=404)

        try:
            filename = f"{model.__name__.lower()}_{format.lower()}_{request.user.username}.{'xlsx' if format=='excel' else format}"
            title = f"Export {model.__name__} — ESFé Mali"
            return ImportExportManager.export_data(qs, format=format, title=title, filename=filename)
        except Exception as e:
            return Response(
                {"ok": False, "error": str(e), "trace": traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
