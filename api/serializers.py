from rest_framework import serializers

from user.models import Member


class UserGetSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, min_value=1)


class ConversationGetSerializer(serializers.Serializer):
    loadFrom = serializers.IntegerField(required=False, min_value=1)
    loadTo = serializers.IntegerField(required=False, min_value=1)
    lastUpdate = serializers.IntegerField(required=True)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=255)
    password = serializers.CharField(required=True, max_length=255)

