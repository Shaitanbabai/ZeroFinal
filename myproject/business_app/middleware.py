from django.shortcuts import redirect
from django.urls import reverse


class CustomLoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and request.path not in [reverse('authorization'), reverse('main_page')]:
            return redirect(reverse('page_errors'))  # Перенаправляем на кастомную страницу ошибок

        response = self.get_response(request)
        return response