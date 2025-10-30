from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("categorie/<slug:slug>/", views.post_by_category, name="post_by_category"),
    path("tag/<slug:slug>/", views.post_by_tag, name="post_by_tag"),
    path("<slug:slug>/", views.post_detail, name="post_detail"),

    # Actions AJAX (commentaires et réactions)
    path("<slug:slug>/comment/new/", views.comment_create, name="comment_create"),
    path("<slug:slug>/comment/<int:parent_id>/reply/", views.comment_reply, name="comment_reply"),
    path("<slug:slug>/react/", views.toggle_reaction, name="toggle_reaction"),
]
