from django.shortcuts import redirect
from django.conf import settings


class LoginRequiredMiddleware:
    """
    Middleware que redirige al login a cualquier usuario no autenticado,
    excepto para las URLs definidas en LOGIN_EXEMPT_URLS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info
            # Permitir acceso a la página de login y al admin
            exempt_urls = [settings.LOGIN_URL, '/admin/']
            if not any(path.startswith(url) for url in exempt_urls):
                return redirect(f'{settings.LOGIN_URL}?next={path}')
        return self.get_response(request)
