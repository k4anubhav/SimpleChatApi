import os
from typing import Union

from channels.db import database_sync_to_async
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from multipledispatch import dispatch

from core.models import ConversationUserMap, Conversation
from user.models import User, MemberToken, Member
from .permissions import IsAuthAndNotBanned
from .serializers import ConversationGetSerializer, LoginSerializer, ConversationSendSerializer, \
    ConversationPostModelSerializer, LogoutSerializer
from .utils import conversationMapToBrief, method_permission_classes

PageSize = int(os.environ.get('PAGE_SIZE', 50))


@api_view(['POST'])
def login(request: Request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(redirect_to='/logout')
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.data['username']
        password = serializer.data['password']
        user, member, token = User.authenticate(request=request._request, name=username, password=password)
        if member and user and token:
            return Response(data={'token': token}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout(request: Request):
    if request.user.is_authenticated:
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.data['allDevices']:
                MemberToken.objects.filter(user=request.user).delete()
            else:
                MemberToken.objects.filter(token=request.token).delete()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class MemberView(APIView):
    @method_permission_classes((IsAuthAndNotBanned,))
    @method_decorator(cache_page(60 * 5))
    def get(self, request: Request, member_id: int, format=None):
        try:
            member = User.objects.get(id=member_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(ConversationPostModelSerializer(member).data, status=status.HTTP_200_OK)


class ConversionBriefView(APIView):
    @method_permission_classes((IsAuthAndNotBanned,))
    def get(self, request: Request, format=None):
        conversationsMap: QuerySet[ConversationUserMap] = ConversationUserMap.objects.filter(
            map_user_id=request.user.member_id).order_by('-map_update').all()
        conversations_brief = conversationMapToBrief(request.user, conversationsMap)
        conversations_brief.sort(key=lambda x: x['lastMsgTime'], reverse=True)
        return Response({"conversations": conversations_brief}, status=status.HTTP_200_OK)


class ConversationView(APIView):

    @staticmethod
    def get_conv(user_or_request: Union[User, Request], pk: int) -> Conversation:
        if isinstance(user_or_request, Request):
            user = user_or_request.user
        else:
            user = user_or_request
        conversation = Conversation.objects.get(con_id=pk)
        conversation.users.index(user.member_id)
        return conversation

    @staticmethod
    @database_sync_to_async
    def get_conv_async(user_or_request: Union[User, Request], pk: int) -> Conversation:
        return ConversationView.get_conv(user_or_request, pk)

    @method_permission_classes((IsAuthAndNotBanned,))
    def get(self, request: Request, pk: int, format=None):
        try:
            conversation = self.get_conv(request, pk)
        except Conversation.DoesNotExist:
            # TODO: create conversation
            return Response({"message": "Conversation does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"message": "You are not in this conversation"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ConversationGetSerializer(data=request.data)
        if serializer.is_valid():
            load_from = serializer.validated_data.get("loadFrom")
            load_to = serializer.validated_data.get("loadTo")
            last_update = serializer.validated_data.get("lastUpdate")
            posts = conversation.get_posts(load_from=load_from, load_to=load_to, last_update=last_update, order_by='chat_id')

            return Response({
                "messages": ConversationPostModelSerializer(posts[:PageSize], many=True).data,
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_permission_classes((IsAuthAndNotBanned,))
    def post(self, request: Request, pk: int, format=None):
        try:
            conversation = self.get_conv(request, pk)
        except Conversation.DoesNotExist:
            return Response({"message": "Conversation does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"message": "You are not in this conversation"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ConversationSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        content = serializer.validated_data.get("content")
        post = conversation.post(
            content=content,
            member_id=request.user.member_id
        )
        return Response({"message": ConversationPostModelSerializer(post).data}, status=status.HTTP_200_OK)

    @method_permission_classes((IsAuthAndNotBanned,))
    def delete(self, request: Request, pk: int, format=None):
        return Response({"message": "Not Implemented"}, status=status.HTTP_400_BAD_REQUEST)
