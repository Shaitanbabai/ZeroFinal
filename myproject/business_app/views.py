import logging

from django.contrib import messages
from django.contrib.auth import (
    authenticate, get_backends, get_permission_codename, login, logout, update_session_auth_hash
)
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from allauth.account.views import email

from .models import Product
from .forms import CustomSignupForm, CustomLoginForm
from .forms import UpdateProfileForm

# Настройка логгера
logger = logging.getLogger(__name__)

def get_user_group_context(user):
    group_names = user.groups.values_list('name', flat=True)
    context = {
        'is_customer': 'customer' in group_names,
        'is_salesman': 'salesman' in group_names
    }
    return context

def redirect_user_based_on_group(user):
    if user.groups.filter(name='customer').exists():
        return redirect('purchase')
    elif user.groups.filter(name='salesman').exists():
        return redirect('sale')
    else:
        return redirect('main_page')

def main_page(request):
    context = {}
    if request.user.is_authenticated:
        context.update(get_user_group_context(request.user))
    return render(request, 'business_app/main_page.html', context)

class AuthorizationView(View):
    def get(self, request, *args, **kwargs):
        form = CustomLoginForm(request=request)
        return render(request, 'business_app/authorization.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = CustomLoginForm(data=request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                backend = get_backends()[0]
                login(request, user, backend=f'{backend.__module__}.{backend.__class__.__name__}')
                logger.info(f"User {user.email} logged in.")
                return redirect_user_based_on_group(user)
            else:
                logger.warning("Authentication failed: user not found.")
                form.add_error(None, "Invalid credentials.")
        context = {'form': form, 'errors': form.errors}
        return render(request, 'business_app/authorization.html', context)


class RegistrationView(View):
    def get(self, request):
        form = CustomSignupForm()
        return render(request, 'business_app/registration.html', {'form': form})

    def post(self, request):
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            login(request, user)
            logger.info(f"User {user.email} registered and logged in.")
            return redirect_user_based_on_group(user)
        context = {'form': form, 'errors': form.errors}
        return render(request, 'business_app/registration.html', context)

def get_permission_for_action(action, model):
    """
    Вспомогательная функция для получения полного имени разрешения
    для заданного действия и модели.
    """
    app_label = model._meta.app_label
    permission_codename = get_permission_codename(action, model._meta)
    return f"{app_label}.{permission_codename}"


@login_required(login_url='page_errors')
def profile(request):
    context = get_user_group_context(request.user)
    return render(request, 'business_app/profile.html', context)


@login_required(login_url='page_errors')
def update_profile(request):
    if request.method == 'POST':
        profile_form = UpdateProfileForm(request.POST, instance=request.user)
        password_form = PasswordChangeForm(user=request.user, data=request.POST)

        if profile_form.is_valid() and password_form.is_valid():
            profile_form.save()
            user = password_form.save()
            update_session_auth_hash(request, user)

            messages.success(request, 'Ваш профиль был успешно обновлён!')
            logout(request)
            return redirect('authorization')
    else:
        profile_form = UpdateProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)

    return render(request, 'update_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })


def logout_view(request):
    logger.info(f"User {request.user.username} logged out.")
    logout(request)
    return redirect(reverse('main_page'))

@login_required(login_url='page_errors')
@permission_required('business_app.customer', login_url='page_errors', raise_exception=True)
def purchase(request):
    context = get_user_group_context(request.user)
    return render(request, 'business_app/purchase.html', context)


@login_required(login_url='page_errors')
@permission_required('business_app.salesman', login_url='page_errors', raise_exception=True)
def sale(request):
    context = get_user_group_context(request.user)
    return render(request, 'business_app/sale.html', context)


@login_required(login_url='page_errors')
@permission_required(get_permission_for_action('change', Product), login_url='page_errors', raise_exception=True)
def update_product(request):
    return render(request, 'business_app/update_product.html')

def handle_permission_denied_or_not_found(request, exception=None):
    """
    Обработчик для ошибок доступа (403) и отсутствующих страниц (404).
    """
    error_message = "Произошла ошибка"
    status_code = 500  # По умолчанию 500, если ошибка не определена

    if exception:
        if isinstance(exception, PermissionDenied):
            error_message = "У вас нет прав для доступа к этой странице."
            status_code = 403
        elif isinstance(exception, Http404):
            error_message = "Страница не найдена."
            status_code = 404

    context = {'error_message': error_message}
    return render(request, 'business_app/page_errors.html', context, status=status_code)
