from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ConversationUserMap, Conversation
from user.models import User
from .permissions import IsAuthAndNotBanned
from .serializers import ConversationGetSerializer, LoginSerializer
from .utils import conversationMapToBrief, method_permission_classes

PageSize = 50


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


class MemberView(APIView):
    @method_permission_classes((IsAuthAndNotBanned,))
    def get(self, request: Request, format=None):
        return Response({"message": "Hello get World"}, status=status.HTTP_200_OK)

    @method_permission_classes((IsAuthAndNotBanned,))
    def post(self, request: Request, format=None):
        return Response({"message": "Hello post World"}, status=status.HTTP_200_OK)


class ConversationView(APIView):
    @method_permission_classes((IsAuthAndNotBanned,))
    def get(self, request: Request, pk=None, format=None):
        if pk is None:
            conversationsMap: QuerySet[ConversationUserMap] = ConversationUserMap.objects.filter(
                map_user_id=request.user.member_id).order_by('-map_update').all()
            conversations_brief = conversationMapToBrief(conversationsMap)
            conversations_brief.sort(key=lambda x: x['lastMsgTime'], reverse=True)
            return Response({"conversations": conversations_brief}, status=status.HTTP_200_OK)
        else:
            try:
                conversation = Conversation.objects.get(con_id=pk, user=request.user.id)
            except Conversation.DoesNotExist:
                return Response({"message": "Conversation does not exist"}, status=status.HTTP_404_NOT_FOUND)
            serializer = ConversationGetSerializer(data=request.data)
            if serializer.is_valid():
                load_from = serializer.validated_data.get("loadFrom")
                load_to = serializer.validated_data.get("loadTo")
                last_update = serializer.validated_data.get("lastUpdate")
                posts = conversation.posts
                filter_args = {}
                if load_from:
                    filter_args["post_id__gt"] = load_from
                if load_to:
                    filter_args["post_id__lt"] = load_to
                if filter_args:
                    posts = posts.filter(**filter_args)
                else:
                    posts = posts.filter(chat_time__gt=last_update)
                return Response({
                    "conversation": conversation,
                    "messages": posts[:PageSize]
                }, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
