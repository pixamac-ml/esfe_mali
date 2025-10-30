from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

from .models import Post, Category, Tag, Comment, Reaction
from .forms import CommentForm


def _is_ajax(request) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


# --------- Page liste des articles ----------
def post_list(request):
    posts = Post.objects.filter(status=Post.PUBLISHED).select_related("category").prefetch_related("tags")
    paginator = Paginator(posts, 9)
    page = request.GET.get("page")
    posts_page = paginator.get_page(page)
    return render(request, "blog/post_list.html", {
        "posts": posts_page,
        "is_paginated": True,
        "page_obj": posts_page
    })


# --------- Page par catégorie ----------
def post_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(status=Post.PUBLISHED, category=category).select_related("category")
    paginator = Paginator(posts, 9)
    page = request.GET.get("page")
    posts_page = paginator.get_page(page)
    return render(request, "blog/post_list.html", {
        "posts": posts_page,
        "current_category": category,
        "is_paginated": True,
        "page_obj": posts_page
    })


# --------- Page par tag ----------
def post_by_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(status=Post.PUBLISHED, tags=tag).select_related("category")
    paginator = Paginator(posts, 9)
    page = request.GET.get("page")
    posts_page = paginator.get_page(page)
    return render(request, "blog/post_list.html", {
        "posts": posts_page,
        "current_tag": tag,
        "is_paginated": True,
        "page_obj": posts_page
    })


# --------- Détail d'un article ----------
def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)
    comments = post.comments.filter(parent__isnull=True, is_approved=True)
    form = CommentForm()
    return render(request, "blog/post_detail.html", {
        "post": post,
        "comments": comments,
        "form": form,
        "like_count": post.reactions.filter(value=1).count(),
        "dislike_count": post.reactions.filter(value=-1).count(),
    })


# --------- Créer un commentaire (AJAX) ----------
@require_POST
def comment_create(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)
    form = CommentForm(request.POST)

    if not form.is_valid():
        if _is_ajax(request):
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return redirect(post.get_absolute_url())

    c = form.save(commit=False)
    c.post = post
    if request.user.is_authenticated:
        c.user = request.user
        c.display_name = request.user.get_username()
        c.is_approved = request.user.is_staff  # auto-approve staff
    c.save()

    if _is_ajax(request):
        if c.is_approved:
            html = render_to_string("blog/partials/comment_item.html", {"c": c}, request=request)
            return JsonResponse({"ok": True, "approved": True, "html": html})
        else:
            return JsonResponse({"ok": True, "approved": False,
                                 "message": "Votre commentaire sera visible après validation."})
    return redirect(post.get_absolute_url())


# --------- Répondre à un commentaire (AJAX) ----------
@require_POST
def comment_reply(request, slug, parent_id):
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)
    parent = get_object_or_404(Comment, id=parent_id, post=post, is_approved=True)
    form = CommentForm(request.POST)

    if not form.is_valid():
        if _is_ajax(request):
            return JsonResponse({"ok": False, "errors": form.errors, "parent_id": parent.id}, status=400)
        return redirect(post.get_absolute_url())

    r = form.save(commit=False)
    r.post = post
    r.parent = parent
    if request.user.is_authenticated:
        r.user = request.user
        r.display_name = request.user.get_username()
        r.is_approved = request.user.is_staff
    r.save()

    if _is_ajax(request):
        if r.is_approved:
            html = render_to_string("blog/partials/reply_item.html", {"r": r}, request=request)
            return JsonResponse({"ok": True, "approved": True, "parent_id": parent.id, "html": html})
        else:
            return JsonResponse({"ok": True, "approved": False, "parent_id": parent.id,
                                 "message": "Votre réponse sera visible après validation."})
    return redirect(post.get_absolute_url())


# --------- Like / Dislike (AJAX) ----------
@require_POST
def toggle_reaction(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)

    try:
        value = int(request.POST.get("value"))
        assert value in (1, -1)
    except Exception:
        return HttpResponseBadRequest("Valeur invalide")

    if request.user.is_authenticated:
        reaction, created = Reaction.objects.get_or_create(
            post=post, user=request.user, defaults={"value": value}
        )
    else:
        fp = (request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR") or "anon")[:64]
        reaction, created = Reaction.objects.get_or_create(
            post=post, guest_fingerprint=fp, defaults={"value": value}
        )

    if not created:
        if reaction.value == value:
            reaction.delete()  # toggle off
        else:
            reaction.value = value
            reaction.save()

    return JsonResponse({
        "likes": post.reactions.filter(value=1).count(),
        "dislikes": post.reactions.filter(value=-1).count(),
    })
