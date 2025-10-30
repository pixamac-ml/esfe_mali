# messenger/urls.py
from django.urls import path
from . import views

app_name = "messenger"

urlpatterns = [
    # 💬 Inbox principale
    path("", views.inbox, name="inbox"),

    # 💬 Conversation (lecture / envoi)
    path("conversation/<uuid:pk>/", views.chat_room, name="chat_room"),
    path("conversation/<uuid:pk>/send/", views.send_message, name="send_message"),

    # ➕ Création conversation
    path("create/", views.create_conversation, name="create_conversation"),

    # 🎥 Appels vidéos
    path("conversation/<uuid:pk>/start-call/", views.start_call, name="start_call"),
    path("call/<slug:room_name>/", views.video_call, name="video_call"),
    path("call/<uuid:call_id>/upload/", views.upload_recording, name="upload_recording"),
]
