from channels.db import database_sync_to_async
from django.db.models import QuerySet

from api.utils import conversationMapToBriefByID
from core.models import ConversationUserMap
from core.utils import SendMessage


class Update:
    def __init__(self):
        self.last_update_chat_id = 0
        self.max_get = 500

    @database_sync_to_async
    def update(self, user_id):
        conversationsMap: QuerySet[ConversationUserMap] = ConversationUserMap.objects.filter(
            map_user_id=user_id, map_unread__gt=0).order_by('-map_update').all()
        conversations_brief = conversationMapToBriefByID(user_id=user_id, data=conversationsMap)
        conversations_brief.sort(key=lambda x: x['lastMsgTime'], reverse=True)
        SendMessage.send_update_message(group_name=f"g{user_id}", data=conversations_brief)

