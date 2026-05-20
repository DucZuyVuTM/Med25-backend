from django.http import HttpResponseForbidden
from django.template.loader import render_to_string


class NginxSecretMiddleware:
    """Block requests that do not originate from the Nginx proxy."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import os
        secret = os.getenv('NGINX_SECRET', '')
        incoming = request.META.get('HTTP_X_NGINX_SECRET', '')

        if secret and incoming != secret:
            csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
            origins_list = [url.strip() for url in csrf_origins.split(',') if url.strip()]

            homepage_url = origins_list[0] if origins_list else 'https://example.onrender.com'

            html = render_to_string('pages/403.html', {'homepage_url': homepage_url}, request=request)
            return HttpResponseForbidden(html)

        return self.get_response(request)
