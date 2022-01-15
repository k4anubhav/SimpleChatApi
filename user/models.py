import os
import re
import time
from typing import Union
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.http import HttpRequest

from user.utils import ipb_oauth_authenticate

assert settings.USE_IPB is not None
UPLOAD_PATH = os.environ.get('UPLOAD_PATH')


# We don't want any changes in ipb database model

class User(AbstractBaseUser):
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)

    # banned from chat api not ipb
    banned = models.BooleanField(default=False)
    member_id = models.IntegerField(unique=True, primary_key=True)

    USERNAME_FIELD = 'name'
    EMAIL_FIELD = 'email'

    @property
    def member(self):
        return Member.objects.get(member_id=self.member_id)

    @staticmethod
    def authenticate(request: HttpRequest, name, password):
        """
        Authenticate user by name|username and password

        :param request: raw request from django, not drf
        :type request: HttpRequest
        :param name: username
        :type name: str
        :param password: password
        :type password: str
        :return: user and its token
        :rtype: (User|None, Member|None, str|None)
        """
        if settings.USE_IPB:
            authenticated, token = ipb_oauth_authenticate(name, password)
            if authenticated:
                # don't use name to identify because it can be changed in ipb and in some cases it can cause privacy issues
                member = Member.objects.get(name=name)
                try:
                    user = User.objects.get(member_id=member.member_id)
                except User.DoesNotExist:
                    user = User.objects.create(member_id=member.member_id, name=name, email=member.email)
                tk = MemberToken.objects.create(ipb_token=token, user=user)
                member.save()
                return user, member, tk.token
        else:
            user: User = django_authenticate(request=request, name=name)
            if user is not None:
                member = Member.objects.get(name=name)
                member.save()
                tk = MemberToken.objects.create(member_id=member.member_id)
                return user, member, tk.token

        return None, None, None


class Member(models.Model):
    class Meta:
        managed = not settings.USE_IPB
        db_table = 'core_members'

    member_id = models.BigAutoField(primary_key=True, null=False)
    name = models.CharField(max_length=255, null=False, unique=True)
    email = models.CharField(max_length=255, null=False, default='')
    joined = models.IntegerField(null=False, default=0)
    last_visit = models.IntegerField(null=False, default=0)
    last_activity = models.IntegerField(null=False, default=0)
    temp_ban = models.IntegerField(null=False, default=0)
    pp_main_photo = models.TextField(null=True)
    timezone = models.CharField(max_length=64, null=True)

    def __str__(self):
        return self.name

    @property
    def banned(self):
        return self.temp_ban > time.time()

    @property
    def profile_photo(self):
        if settings.USE_IPB:
            if re.match(r'.+\.(gif|jpe?g|bmp|png)$', self.pp_main_photo):
                return UPLOAD_PATH + self.pp_main_photo
            else:
                return None
        else:
            return self.pp_main_photo


class MemberToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, null=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    ipb_token = models.CharField(max_length=255, null=True)

    @property
    def member(self):
        return Member.objects.get(member_id=self.user.member_id)

    @staticmethod
    def get_member_from_token(token) -> Union[Member, None]:
        try:
            return MemberToken.objects.get(token=token).member
        except MemberToken.DoesNotExist:
            return None

    @staticmethod
    def get_member_id_from_token(token) -> Union[int, None]:
        try:
            return MemberToken.objects.get(token=token).member_id
        except MemberToken.DoesNotExist:
            return None

    def __str__(self):
        return self.token

    @classmethod
    def generate_token(cls) -> str:
        return uuid4().__str__()


@receiver(pre_save, sender=User)
def pre_save_user(sender, instance, **kwargs):
    if instance.pk is not None:
        member = Member.objects.get(member_id=instance.member_id)
        member.save()


@receiver(pre_save, sender=Member)
def memberPreSave(sender, instance, **kwargs):
    current_time = int(time.time())
    if instance.pk is None:
        instance.joined = current_time
        instance.last_visit = current_time
        instance.last_activity = current_time
    else:
        instance.last_activity = current_time


@receiver(pre_save, sender=MemberToken)
def memberTokenPreSave(sender, instance, **kwargs):
    if instance.pk is None:
        instance.created = int(time.time())
    if instance.token is None or instance.token == '':
        while True:
            token = MemberToken.generate_token()
            if not MemberToken.objects.filter(token=token).exists():
                instance.token = token
                break
