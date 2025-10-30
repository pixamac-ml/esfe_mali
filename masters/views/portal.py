# masters/views/portal.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

def portal_landing(request):
    return render(request, "masters/portal.html")
