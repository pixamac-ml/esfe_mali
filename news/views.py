from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import News


from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import News


def news_list(request):
    qs = News.objects.all()
    paginator = Paginator(qs, 9)
    page = request.GET.get("page")
    news_page = paginator.get_page(page)

    # AJAX → on renvoie juste le fragment HTML
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "news/_news_items.html",
            {"news_list": news_page, "page_obj": news_page},
            request=request,
        )
        return JsonResponse({"html": html})

    # Normal → page complète
    return render(request, "news/news_list.html", {"news_list": news_page, "page_obj": news_page})


def news_detail(request, slug):
    news = get_object_or_404(News, slug=slug)
    return render(request, "news/news_detail.html", {"news": news})
