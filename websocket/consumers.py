import os
from typing import Dict, Optional

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from api.utils import postSerializerAsync
from api.views import ConversationView
from core.models import Conversation
from user.models import User
from websocket.serializers import BaseEventSerializer, GetConversationSerializerData, Response, \
    SetConversationSerializer

PageSize = int(os.environ.get('PAGE_SIZE', 50))

UPDATE_TIME = os.environ.get('UPDATE_TIME')
assert UPDATE_TIME


def consumer_logged_in_req(func):
    async def wrapper(*args, **kwargs):
        consumer: AsyncJsonWebsocketConsumer = args[0]
        if (not consumer.scope['user'].is_authenticated) or consumer.scope['user'].banned:
            return await consumer.close()
        return await func(*args, **kwargs)

    return wrapper


class BaseConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: User

    @consumer_logged_in_req
    async def connect(self):
        self.user = self.scope['user']
        await self.accept()


class ChatConsumer(BaseConsumer):
    consumers = {}
    """
    :type consumers: Dict[str, BaseConsumer]
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_activity = None
        self.con_id: Optional[int] = None

    async def connect(self):
        await super().connect()
        if (_x := self.consumers.get(self.user.name)) and not _x.close():
            ChatConsumer.consumers[self.user.name] = self

    async def disconnect(self, close_code):
        ChatConsumer.consumers.pop(self.user.name, None)
        await super(ChatConsumer, self).disconnect(close_code)

    async def update(self, content):
        ...

    async def receive_json(self, content: Dict, **kwargs):
        print(content)
        if (serialized := BaseEventSerializer(data=content)) is None or serialized.is_valid():
            content = serialized.validated_data
            if content['type'] == 'get-conv':
                return await self.handle_get_conv(content['data'])
            elif content['type'] == 'set-chat-id':
                return await self.handle_set_chat_id(content['data'])

        return await self.send_error(message="Invalid data", code=400, from_command=content.get('type'))

    async def send_error(self, message: str, from_command: str, code: int = 400):
        return await self.send_json(Response.error_response(message=message, code=code, from_command=from_command))

    async def send_response(self, _type: str, data: Dict):
        return await self.send_json(Response.response(_type, data))

    async def handle_get_conv(self, data: Dict):
        if (serialized := GetConversationSerializerData(data=data)) is None or serialized.is_valid():
            data = serialized.validated_data
            if not (pk := data.get('chatID')):
                if not (pk := self.con_id):
                    return await self.send_error('No chatID', from_command="get-conv")
            try:
                conversation = await ConversationView.get_conv_async(self.user, pk)
            except Conversation.DoesNotExist:
                # TODO: create conversation
                if self.con_id == pk:
                    self.con_id = None
                return await self.send_error(message="Conversation does not exist", code=404, from_command="get-conv")
            except ValueError:
                if self.con_id == pk:
                    self.con_id = None
                return await self.send_error(message="You are not in this conversation", code=403,
                                             from_command="get-conv")

            load_from = data.get("loadFrom")
            load_to = data.get("loadTo")
            last_update = data.get("lastUpdate")
            posts = conversation.get_posts(load_from=load_from, load_to=load_to, last_update=last_update,
                                           order_by='chat_id')
            return await self.send_response('get-conv', {
                "messages": (await postSerializerAsync(posts=posts[:PageSize], many=True))
            })
        else:
            return await self.send_error(message=serialized.errors.__str__(), from_command="get-conv")

    async def handle_set_chat_id(self, data: Dict):
        if (serialized := SetConversationSerializer(data=data)) is None or serialized.is_valid():
            data = serialized.validated_data
            pk = data['chatID']
            try:
                await ConversationView.get_conv_async(self.user, pk=pk)
            except Conversation.DoesNotExist:
                # TODO: create conversation
                if self.con_id == pk:
                    self.con_id = None
                return await self.send_error(message="Conversation does not exist", code=404, from_command="set-chatID")
            except ValueError:
                if self.con_id == pk:
                    self.con_id = None
                return await self.send_error(message="You are not in this conversation", code=403,
                                             from_command="set-chatID")

            self.con_id = pk
            return await self.send_response('set-chatID', {
                "success": True
            })
