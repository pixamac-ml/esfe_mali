import json, secrets
from django.contrib.auth.decorators import login_required
from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    Http404,
)
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Conversation, ConversationParticipant, Message, CallSession
from .utils import is_ajax, user_queryset_for_messenger

User = get_user_model()


# ==============================
# 🔐 sécurité
# ==============================
def ensure_member(user, conversation: Conversation):
    if not ConversationParticipant.objects.filter(
        conversation=conversation, user=user
    ).exists():
        raise Http404("Vous n'avez pas accès à cette conversation.")


# ==============================
# 📥 Inbox (liste des convos)
# ==============================
@login_required
def inbox(request):
    """
    - si appelé en AJAX → on envoie juste le fragment (pour dashboard)
    - si appelé direct → page complète (utile si on ouvre /messenger/ direct)
    """
    convs = (
        ConversationParticipant.objects.filter(user=request.user)
        .select_related("conversation")
        .order_by("-conversation__created_at")
    )
    users = user_queryset_for_messenger(request.user)

    ctx = {
        "convs": convs,
        "users": users,
        "me": request.user,
    }

    if is_ajax(request):
        return render(request, "messenger/inbox_fragment.html", ctx)
    return render(request, "messenger/inbox_page.html", ctx)


# ==============================
# 💬 Affichage d'une conversation
# ==============================
@login_required
def chat_room(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    ensure_member(request.user, conv)

    messages = conv.messages.select_related("sender").order_by("created_at")[:500]

    # on met à jour la dernière lecture
    ConversationParticipant.objects.filter(
        conversation=conv, user=request.user
    ).update(last_read_at=timezone.now())

    ctx = {
        "conv": conv,
        "messages": messages,
        "self_id": request.user.id,
    }

    if is_ajax(request):
        return render(request, "messenger/chat_room_fragment.html", ctx)
    return render(request, "messenger/chat_room_page.html", ctx)


# ==============================
# 🆕 Création conversation (AJAX)
# ==============================
@login_required
@require_POST
def create_conversation(request):
    """
    Accepte :
    - JSON : { "title": "...", "users": ["3","8","12"] }
    - ou POST classique

    Retourne : { ok: true, chat_url: "/messenger/conversation/<uuid>/?fragment=1" }
    """
    if request.content_type.startswith("application/json"):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return HttpResponseBadRequest("invalid-json")
    else:
        payload = request.POST

    title = (payload.get("title") or "").strip()
    users_ids = payload.get("users") or payload.get("participants") or ""

    if isinstance(users_ids, str):
        # cas "1,2,3"
        users_ids = [x.strip() for x in users_ids.split(",") if x.strip()]

    # on crée la convo
    conv = Conversation.objects.create(
        title=title or "",
        created_by=request.user,
        is_group=len(users_ids) > 1,
    )

    # le créateur est participant
    ConversationParticipant.objects.create(
        conversation=conv,
        user=request.user,
        role=getattr(request.user, "role", "") or "",
    )

    # on ajoute les participants
    for uid in users_ids:
        try:
            u = User.objects.get(pk=uid)
        except User.DoesNotExist:
            continue
        ConversationParticipant.objects.get_or_create(
            conversation=conv,
            user=u,
            defaults={"role": getattr(u, "role", "") or ""},
        )

    chat_url = redirect("messenger:chat_room", pk=conv.pk).url + "?fragment=1"
    return JsonResponse({"ok": True, "chat_url": chat_url})


# ==============================
# ✉️ Envoi d'un message (fallback HTTP)
# ==============================
@login_required
@require_POST
def send_message(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    ensure_member(request.user, conv)

    text = (request.POST.get("text") or "").strip()
    file = request.FILES.get("file")

    if not text and not file:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)

    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        text=text,
        file=file,
    )

    # si c'est du AJAX → on renvoie le fragment du message
    if is_ajax(request):
        return render(
            request,
            "messenger/_message_item.html",
            {"m": msg, "self_id": request.user.id},
        )

    # sinon on repart sur la page
    return redirect("messenger:chat_room", pk=pk)


# ==============================
# 🎥 Démarrer un appel
# ==============================
@login_required
def start_call(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    ensure_member(request.user, conv)

    room = secrets.token_urlsafe(8).replace("_", "-")
    call = CallSession.objects.create(
        conversation=conv,
        host=request.user,
        room_name=room,
        status="INIT",
    )

    # si c'est injecté dans le dashboard → fragment
    if is_ajax(request):
        return render(request, "messenger/video_call_fragment.html", {"call": call})

    # sinon → page complète
    return redirect("messenger:video_call", room_name=call.room_name)


# ==============================
# 🎥 Rejoindre un appel
# ==============================
@login_required
def video_call(request, room_name):
    call = get_object_or_404(CallSession, room_name=room_name)
    ensure_member(request.user, call.conversation)

    if call.status == "INIT":
        call.start()

    ctx = {"call": call}

    if is_ajax(request):
        return render(request, "messenger/video_call_fragment.html", ctx)
    return render(request, "messenger/video_call_page.html", ctx)


# ==============================
# 📁 Upload d'enregistrement
# ==============================
@csrf_exempt
@require_POST
@login_required
def upload_recording(request, call_id):
    call = get_object_or_404(CallSession, pk=call_id)
    ensure_member(request.user, call.conversation)

    file = request.FILES.get("file")
    if not file:
        return JsonResponse({"ok": False, "error": "no-file"}, status=400)

    call.local_file.save(f"call-{call.id}.webm", file)
    call.bytes_size = call.local_file.size or 0
    call.duration_sec = int(request.POST.get("duration", 0) or 0)
    call.end()

    return JsonResponse({"ok": True, "file": call.local_file.url})
