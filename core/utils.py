from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class SendMessage:

    @staticmethod
    def _send(group_name, data):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name, data
        )

    @staticmethod
    def send_update_message(group_name, data):
        SendMessage._send(group_name, {
            'type': 'update',
            'data': data
        })

    @staticmethod
    def send_chat_message(group_name, data):
        SendMessage._send(group_name, {
            'type': 'chat',
            'data': data
        })
