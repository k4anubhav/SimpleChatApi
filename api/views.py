import os

from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ConversationUserMap, Conversation
from user.models import User, MemberToken
from .permissions import IsAuthAndNotBanned
from .serializers import ConversationGetSerializer, LoginSerializer, ConversationSendSerializer, \
    ConversationPostModelSerializer, LogoutSerializer, ErrorSerializer, LoginResponseSerializer, \
    ConversationInfoSerializer
from .utils import conversationMapToBrief, method_permission_classes, get_conv

PageSize = int(os.environ.get('PAGE_SIZE', 50))


@extend_schema(
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(LoginResponseSerializer, description='Successful login'),
        400: OpenApiResponse(ErrorSerializer, description='Invalid login data'),
        401: OpenApiResponse(ErrorSerializer, description='Invalid login data'),
    },
    tags=['auth'],
    methods=['POST'],
)
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
            return Response(LoginResponseSerializer(token=token).data, status=status.HTTP_200_OK)
        else:
            return Response(ErrorSerializer(error='Invalid credentials'), status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response(ErrorSerializer(error='Invalid Params', data=serializer.errors).data,
                        status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=LogoutSerializer,
    responses={
        200: OpenApiResponse(description='Successful login'),
        400: OpenApiResponse(description='Invalid login data'),
        401: OpenApiResponse(description='Invalid login data'),
    },
    tags=['auth'],
    methods=['POST']
)
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
            return Response(ErrorSerializer(error='Invalid Params', data=serializer.errors).data,
                            status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class MemberView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(name='member_id', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                             description='Member ID')
        ],
        responses={
            200: OpenApiResponse(ConversationPostModelSerializer, description='User data'),
            400: OpenApiResponse(ErrorSerializer, description='Credentials are invalid'),
            404: OpenApiResponse(ErrorSerializer, description='User not found'),
        },
        tags=['Member'],
        methods=['GET']
    )
    @method_permission_classes((IsAuthAndNotBanned,))
    @method_decorator(cache_page(60 * 5))
    def get(self, request: Request, member_id: int, format=None):
        try:
            member = User.objects.get(id=member_id)
        except User.DoesNotExist:
            return Response(ErrorSerializer(error='Not Found').data, status=status.HTTP_404_NOT_FOUND)

        return Response(ConversationPostModelSerializer(member).data, status=status.HTTP_200_OK)


class ConversionBriefView(APIView):
    @extend_schema(
        responses={
            200: OpenApiResponse(ConversationInfoSerializer(many=True), description='Conversations Info'),
            400: OpenApiResponse(ErrorSerializer, description='Credentials are invalid'),
        },
        tags=['ConversionBrief'],
        methods=['GET'],
        operation_id='get_conversations'
    )
    @method_permission_classes((IsAuthAndNotBanned,))
    def get(self, request: Request, format=None):
        conversationsMap: QuerySet[ConversationUserMap] = ConversationUserMap.objects.filter(
            map_user_id=request.user.member_id).order_by('-map_update').all()
        conversations_brief = conversationMapToBrief(request.user, conversationsMap)
        conversations_brief.sort(key=lambda x: x['lastMsgTime'], reverse=True)
        return Response(conversations_brief, status=status.HTTP_200_OK)


class ConversationView(APIView):
    @extend_schema(
        request=ConversationGetSerializer,
        parameters=[
            OpenApiParameter(name='pk', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                             description='Conv ID')
        ],
        responses={
            200: OpenApiResponse(response=ConversationPostModelSerializer(many=True), description='Messages data'),
            400: OpenApiResponse(ErrorSerializer, description='Credentials are invalid'),
            404: OpenApiResponse(ErrorSerializer, description='Conversation not found'),
            403: OpenApiResponse(ErrorSerializer, description='Conversation forbidden'),
        },
        tags=['Conversation'],
        methods=['GET']
    )
    @method_permission_classes((IsAuthAndNotBanned,))
    # pylint: disable=unused-argument
    def get(self, request: Request, pk: int, format=None):
        try:
            conversation = get_conv(request, pk)
        except Conversation.DoesNotExist:
            # TODO: create conversation
            return Response(ErrorSerializer(error="Conversation does not exist").data, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(ErrorSerializer(error="You are not in this conversation").data,
                            status=status.HTTP_403_FORBIDDEN)

        serializer = ConversationGetSerializer(data=request.data)
        if serializer.is_valid():
            load_from = serializer.validated_data.get("loadFrom")
            load_to = serializer.validated_data.get("loadTo")
            last_update = serializer.validated_data.get("lastUpdate")
            posts = conversation.get_posts(load_from=load_from, load_to=load_to, last_update=last_update,
                                           order_by='chat_id', max_size=PageSize)

            return Response(ConversationPostModelSerializer(posts, many=True).data, status=status.HTTP_200_OK)
        else:
            return Response(ErrorSerializer(error='Invalid Params', data=serializer.errors).data,
                            status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=ConversationSendSerializer,
        parameters=[
            OpenApiParameter(name='pk', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                             description='Conv ID')
        ],
        responses={
            200: OpenApiResponse(ConversationPostModelSerializer, description='Message data'),
            400: OpenApiResponse(ErrorSerializer, description='Credentials are invalid'),
            404: OpenApiResponse(ErrorSerializer, description='Conversation not found'),
            403: OpenApiResponse(ErrorSerializer, description='Conversation forbidden'),
        },
        tags=['Conversation'],
        methods=['POST']
    )
    @method_permission_classes((IsAuthAndNotBanned,))
    def post(self, request: Request, pk: int, format=None):
        try:
            conversation = get_conv(request, pk)
        except Conversation.DoesNotExist:
            return Response(ErrorSerializer(error="Conversation does not exist").data, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(ErrorSerializer(error="You are not in this conversation").data,
                            status=status.HTTP_403_FORBIDDEN)

        serializer = ConversationSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(ErrorSerializer(error='Invalid Params', data=serializer.errors).data,
                            status=status.HTTP_400_BAD_REQUEST)

        content = serializer.validated_data.get("content")
        post = conversation.post(
            content=content,
            member_id=request.user.member_id
        )
        return Response(ConversationPostModelSerializer(post).data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='pk', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                             description='Conv ID')
        ],
        responses={
            400: OpenApiResponse(ErrorSerializer, description='Credentials are invalid'),
        },
        tags=['Conversation'],
        methods=['DELETE']
    )
    @method_permission_classes((IsAuthAndNotBanned,))
    def delete(self, request: Request, pk: int, format=None):
        return Response(ErrorSerializer(error="Not Implemented").data, status=status.HTTP_400_BAD_REQUEST)
