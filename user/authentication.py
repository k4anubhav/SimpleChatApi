from rest_framework import authentication
from rest_framework import exceptions

from .models import MemberToken


class TokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get('X-API-Key')
        if not token:
            return None
        request.token = None
        try:
            request.token = token
            user = MemberToken.objects.get(token=token).user
        except MemberToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid Token')
        return user, None
