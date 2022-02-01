import time
from typing import List, Union, Optional, Coroutine, Any, Awaitable

from channels.db import database_sync_to_async
from django.db.models import QuerySet
from rest_framework.request import Request

from api.serializers import ConversationPostModelSerializer, ConversationInfoSerializer
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
):
    ret = []
    for _conv in data:
        conv: Conversation = _conv.conversation
        if last_post := conv.last_post:
            ret.append(
                ConversationInfoSerializer(
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
                ).data
            )
    return ret


def conversationMapToBrief(
        user: User,
        data: Union[QuerySet[ConversationUserMap], List[ConversationUserMap]]
) -> List:
    return conversationMapToBriefByID(user.member_id, data)


@database_sync_to_async
def postSerializerAsync(posts, *args, **kwargs):
    return ConversationPostModelSerializer(posts, *args, **kwargs).data


def get_conv(
        user_or_request: Union[User, Request],
        pk: int,
        _async: bool = False
) -> Union[Conversation, Awaitable[Conversation]]:
    def _get_conv(_user_or_request: Union[User, Request], _pk: int):
        if isinstance(user_or_request, Request):
            user = user_or_request.user
        else:
            user = user_or_request

        conversation = Conversation.objects.get(con_id=pk)
        conversation.users.index(user.member_id)
        return conversation

    if _async:
        return database_sync_to_async(_get_conv)(user_or_request, pk)
    else:
        return _get_conv(user_or_request, pk)
