from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

from user.models import MemberToken


@database_sync_to_async
def get_user(token):
    try:
        token = MemberToken.objects.get(token=token)
        return token.user
    except MemberToken.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        token = None
        headers = scope['headers']
        for header in headers:
            if header[0] == b'x-api-key':
                token = header[1].decode()
                break

        scope['user'] = AnonymousUser() if token is None else await get_user(token)
        return await super().__call__(scope, receive, send)
