import time
from typing import List, Union, Optional

from channels.db import database_sync_to_async
from django.db.models import QuerySet

from api.TypedResponse import ConversationBrief
from api.serializers import ConversationPostModelSerializer
from core.models import ConversationUserMap, Conversation
from user.models import Member, User


# from https://stackoverflow.com/questions/19773869/django-rest-framework-separate-permissions-per-methods
def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            # this call is needed for request permissions
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


def getConvIcon(user_id: int, conv_id: int) -> Optional[str]:
    conv = Conversation.objects.get(con_id=conv_id)
    if conv.isGroup():
        # TODO: get icon for group
        return None
    else:
        users_id = conv.users
        try:
            users_id.remove(user_id)
            return Member.objects.get(member_id=users_id[0]).profile_photo
        except ValueError or IndexError:
            return None


def conversationMapToBriefByID(
        user_id: int,
        data: Union[QuerySet[ConversationUserMap], List[ConversationUserMap]]
) -> List[ConversationBrief]:
    ret: List[ConversationBrief] = []
    for _conv in data:
        conv: Conversation = _conv.conversation
        if last_post := conv.last_post:
            ret.append(
                ConversationBrief(
                    icon=getConvIcon(user_id, _conv.map_con_id),
                    id=_conv.map_con_id,
                    inDay=24 * 60 * 60 > (time.time() - _conv.map_update),
                    isGroup=conv.isGroup(),
                    isOnline=1 == _conv.map_online,
                    lastMsg=last_post.chat_content,
                    lastMsgID=last_post.chat_id,
                    lastMsgTime=last_post.chat_time,
                    title=conv.con_name,
                    unread=_conv.map_unread,
                    update=_conv.map_update,
                )
            )
    return ret


def conversationMapToBrief(
        user: User,
        data: Union[QuerySet[ConversationUserMap], List[ConversationUserMap]]
) -> List[ConversationBrief]:
    return conversationMapToBriefByID(user.member_id, data)


@database_sync_to_async
def postSerializerAsync(posts, *args, **kwargs):
    return ConversationPostModelSerializer(posts, *args, **kwargs).data
