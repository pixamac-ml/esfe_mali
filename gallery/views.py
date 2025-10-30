from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Album

def album_list(request):
    albums = Album.objects.all().order_by("-created_at")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("gallery/_album_items.html", {"albums": albums}, request=request)
        return JsonResponse({"html": html})
    return render(request, "gallery/album_list.html", {"albums": albums})

def album_detail(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("gallery/_album_detail.html", {"album": album}, request=request)
        return JsonResponse({"html": html})
    return render(request, "gallery/album_detail.html", {"album": album})
