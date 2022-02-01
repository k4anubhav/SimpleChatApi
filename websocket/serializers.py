from rest_framework import serializers

from api.serializers import ConversationGetSerializer


class BaseEventSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=255)
    data = serializers.JSONField()


class GetConversationSerializerData(ConversationGetSerializer):
    chatID = serializers.IntegerField(min_value=1, required=False)


class SetConversationSerializer(serializers.Serializer):
    chatID = serializers.IntegerField(min_value=1, required=True)


class SendMessageSerializer(serializers.Serializer):
    chatID = serializers.IntegerField(min_value=1, required=False)
    message = serializers.CharField(max_length=255, required=True)


class Response:
    @staticmethod
    def response(_type: str, data: dict) -> dict:
        return {
            'type': _type,
            'data': data
        }

    @staticmethod
    def error_response(message: str, from_command: str, code: int = 400) -> dict:
        return Response.response(
            _type="error",
            data={
                "from": from_command,
                "message": message,
                "code": code
            }
        )
