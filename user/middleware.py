from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin

from user.models import MemberToken


class TokenMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)

    def process_request(self, request: HttpRequest):
        token = request.headers.get('X-API-Key')
        if token and not request.user.is_authenticated:
            request.token = token
            request.user = MemberToken.objects.get(token=token).user
        else:
            request.token = None
