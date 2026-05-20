from django.http import HttpResponseForbidden


class NginxSecretMiddleware:
    """Block requests that do not originate from the Nginx proxy."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import os
        secret = os.getenv('NGINX_SECRET', '')
        incoming = request.META.get('HTTP_X_NGINX_SECRET', '')

        if secret and incoming != secret:
            return HttpResponseForbidden('Direct access not allowed.')

        return self.get_response(request)
