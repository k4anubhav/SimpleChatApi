
# https://stackoverflow.com/a/47888695/14312439
class CsrfExemptSessionAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # add CSRF exempt session to every request
        setattr(request, '_dont_enforce_csrf_checks', True)
        response = self.get_response(request)
        return response
