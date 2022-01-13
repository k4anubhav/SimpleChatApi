# from https://stackoverflow.com/questions/19773869/django-rest-framework-separate-permissions-per-methods
import time
from typing import List, Union

from django.db.models import QuerySet

from api.TypedResponse import ConversationBrief
from core.models import ConversationUserMap, Conversation


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            # this call is needed for request permissions
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


def conversationMapToBrief(
        data: Union[QuerySet[ConversationUserMap], List[ConversationUserMap]]
) -> List[ConversationBrief]:

    ret: List[ConversationBrief] = []
    for _conv in data:
        conv: Conversation = _conv.conversation
        if last_post := conv.last_post:
            ret.append(
                ConversationBrief(
                    icon='',  # TODO: get icon
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

def ipb_login(username, password):
    @staticmethod
    def authenticate(username: str, password: str):
        """
        authenticate users

        :param username: username/email of user
        :type username: str
        :param password: pas
        :type password: password
        :return: Tuple of is user authenticated and user object
        :rtype: (bool, Account)
        """
        authenticated, token = oauth_authenticate(username, password)
        if not authenticated:
            return False, None

        token_match_queryset = Account.objects.filter(token=token)

        if token_match_queryset.exists():
            return True, token_match_queryset[0]

        user_id, username = get_user_info(token)

        if (not user_id) or (not username):
            return False, None

        user_queryset = Account.objects.filter(user_id=user_id)
        if user_queryset.exists():
            user: Account = user_queryset[0]
            user.token = token
            user.save()
            return True, user

        user = Account.objects.create_user(user_id=user_id, username=username, token=token)
        return True, user


