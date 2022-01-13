import time
from typing import List

from django.conf import settings
from django.db import models

from user.models import Member


# No ForeignKey is Used for any of the following models


class Conversation(models.Model):
    class Meta:
        managed = not settings.USE_IPB
        db_table = 'chatbox_conversations'
        indexes = [
            models.Index(fields=['con_id', 'con_starter_id', 'con_started_date'], name='convo_id'),
            models.Index(fields=['con_id', 'con_lastID', 'con_lastChat'], name='convo_last_chat'),
        ]

    con_id = models.BigAutoField(primary_key=True)
    con_starter_id = models.BigIntegerField(null=False, default=0)
    con_started_date = models.IntegerField(null=False, default=0)
    con_lastID = models.IntegerField(null=False, default=0)
    con_lastChat = models.TextField(null=True)
    con_name = models.TextField(null=False)
    con_isGroup = models.IntegerField(null=False, default=0)
    con_group_options = models.TextField(null=True)
    con_users = models.TextField(null=True)

    def __str__(self):
        return self.con_name

    @property
    def last_post(self):
        return ConversationPost.objects.filter(chat_con=self.con_id).order_by('-chat_time').first()

    @property
    def posts(self):
        return ConversationPost.objects.filter(chat_con=self.con_id).order_by('-chat_time')

    def isGroup(self):
        return self.con_isGroup == 1

    def users(self) -> List[int]:
        if self.con_users:
            return []
        return list(map(int, self.con_users.split(',')))


class ConversationUserMap(models.Model):
    class Meta:

        managed = not settings.USE_IPB
        db_table = 'chatbox_conversations_user_map'
        indexes = [
            models.Index(fields=['map_id', 'map_update', 'map_user_id', 'map_online'], name='map_id'),
            models.Index(fields=['map_user_id'], name='map_user_id'),
        ]

    map_id = models.BigAutoField(primary_key=True)
    map_user_id = models.BigIntegerField(null=False, default=0)
    map_con_id = models.BigIntegerField(null=False, default=0)
    map_unread = models.IntegerField(null=False, default=0)
    map_online = models.SmallIntegerField(null=False, default=1)
    map_update = models.IntegerField(null=False, default=0)

    @property
    def conversation(self):
        return Conversation.objects.get(con_id=self.map_con_id)


class ConversationPost(models.Model):
    class Meta:
        managed = not settings.USE_IPB
        db_table = 'chatbox_conversations_posts'
        indexes = [
            models.Index(fields=['chat_time', 'chat_member_id', 'chat_con', 'chat_id'], name='convo_index'),
        ]

    chat_id = models.BigAutoField(primary_key=True)
    chat_time = models.IntegerField(null=False, default=lambda: int(time.time()))
    chat_con = models.BigIntegerField(null=False, default=0)
    chat_content = models.TextField(null=False)
    chat_member_id = models.BigIntegerField(null=False, default=0)
    chat_ip_address = models.CharField(max_length=46, null=False, default='0')
    chat_title = models.CharField(max_length=255, null=True)
    chat_title_furl = models.CharField(max_length=255, null=True)
    chat_fileID = models.IntegerField(null=False, default=0)
    chat_sys = models.TextField(null=True)

    def __str__(self):
        return self.chat_content

    @property
    def conversation(self):
        return Conversation.objects.get(con_id=self.chat_con)

    @property
    def member(self):
        return Member.objects.get(id=self.chat_member_id)

    def isSystem(self):
        return self.chat_sys is not None

    def isFile(self):
        return self.chat_fileID > 0