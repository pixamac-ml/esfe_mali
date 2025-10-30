from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Accède à dictionary[key] dans les templates.
    Usage: {{ my_dict|get_item:object.id }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def grade_class(value):
    """
    Retourne une classe CSS selon la note (/20).
    >=10 : vert ; <10 : rouge ; sinon gris.
    """
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "text-slate-600"
    return "text-emerald-600" if n >= 10 else "text-rose-600"
