from django.conf import settings

from .models import ConversationPost, Conversation, ConversationUserMap


class MyDBRouter(object):

    def db_for_read(self, model, **hints):
        """ reading SomeModel from otherdb """
        if model in [ConversationPost, Conversation, ConversationUserMap] and settings.USE_IPB:
            return 'chats'
        return None

    def db_for_write(self, model, **hints):
        """ writing SomeModel to otherdb """
        if model in [ConversationPost, Conversation, ConversationUserMap] and settings.USE_IPB:
            return 'chats'
        return None
