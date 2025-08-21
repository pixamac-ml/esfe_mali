# Admissions app (ESFé)

## Installation rapide
1. Ajouter `"admissions"` et `"programs"` dans `INSTALLED_APPS`.
2. `python manage.py makemigrations admissions && python manage.py migrate`
3. Inclure les URLs: `path("admissions/", include("admissions.urls"))`
4. Lier le bouton "S’inscrire" depuis `programs:detail` vers `admissions:apply_from_program`.

## Vues incluses
- Public:
  - `apply_from_program/<slug>/` (formulaire prérempli avec la formation)
  - `apply/` (formulaire générique)
  - `thanks/<ref_code>/`
- Admin simple (login staff requis) :
  - `admin/list/`, `admin/create/`, `admin/<ref>/`, `admin/<ref>/edit/`, `admin/<ref>/delete/`

## À brancher ensuite
- Déclenchement WhatsApp (Cloud API) ou Checkout PSP dans `apply_*`.
- Webhooks PSP pour marquer `PAIEMENT_OK`.
