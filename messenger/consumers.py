import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ConversationParticipant, Message


@database_sync_to_async
def is_member(conv_id, user_id):
    return ConversationParticipant.objects.filter(
        conversation_id=conv_id, user_id=user_id
    ).exists()


@database_sync_to_async
def create_message(conv_id, user, text):
    m = Message.objects.create(conversation_id=conv_id, sender=user, text=text)
    return {
        "id": m.id,
        "text": m.text,
        "sender_id": user.id,
        "sender_name": user.get_full_name() or user.username,
        "created_at": m.created_at.isoformat(),
    }


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket /ws/chat/<conversation_id>/
    Diffuse les messages + peut servir pour le “seen”
    """

    async def connect(self):
        self.conv_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"chat_{self.conv_id}"
        user = self.scope.get("user")

        if not user or isinstance(user, AnonymousUser):
            await self.close(code=4001)
            return

        allowed = await is_member(self.conv_id, user.id)
        if not allowed:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data or "{}")
        msg_type = data.get("type")

        if msg_type == "message":
            text = (data.get("text") or "").strip()
            if not text:
                return
            user = self.scope["user"]
            payload = await create_message(self.conv_id, user, text)
            payload["event"] = "message"
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat_event", "payload": payload}
            )

    async def chat_event(self, event):
        await self.send(text_data=json.dumps(event["payload"]))


# Pour la signalisation WebRTC
class CallSignalingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.group_name = f"call_{self.room_name}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data or "{}")
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "signal_event", "payload": data}
        )

    async def signal_event(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
