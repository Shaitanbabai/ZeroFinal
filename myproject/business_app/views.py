import logging

from django.contrib import messages
from django.contrib.auth import (
    authenticate, get_backends, get_permission_codename, login, logout, update_session_auth_hash
)
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import Group
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
    """
    Возвращает словарь с информацией о принадлежности пользователя к группам.
    """
    group_names = user.groups.values_list('name', flat=True)
    context = {
        'is_customer': 'customer' in group_names,
        'is_salesman': 'salesman' in group_names
    }
    return context

def main_page(request):
    context = {}
    if request.user.is_authenticated:
        context.update(get_user_group_context(request.user))
    return render(request, 'business_app/main_page.html', context)


class AuthorizationView(View):
    def get(self, request):
        form = CustomLoginForm()
        return render(request, 'account/login.html', {'form': form})

    def post(self, request):
        form = CustomLoginForm(data=request.POST)

        if form.is_valid():
            # Получаем email и пароль
            email = form.cleaned_data.get('email')  # Используем 'email'
            password = form.cleaned_data.get('password')

            # Аутентификация пользователя по email и паролю
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                logger.info(f"User {user.email} logged in.")
                return redirect_user_based_on_group(user)
            else:
                logger.warning("Authentication failed: user not found.")
                form.add_error(None, "Invalid credentials.")

        return render(request, 'account/login.html', {'form': form})


class RegistrationView(View):
    def get(self, request):
        form = CustomSignupForm()
        return render(request, 'account/signup.html', {'form': form})

    def post(self, request):
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            customer_group = Group.objects.get(name='customer')
            user.groups.add(customer_group)
            backend = get_backends()[0]  # Берем первый доступный бэкенд
            user.backend = f'{backend.__module__}.{backend.__class__.__name__}'
            email(request, user)
            logger.info(f"New user {user.email} registered and logged in.")
            login(request, user)
            return redirect(reverse('purchase'))
        else:
            return render(request, 'account/signup.html', {'form': form, 'errors': form.errors})


# @login_required
# @permission_required('business_app.customer', login_url='/')
# def purchase(request):
#     return render(request, 'business_app/purchase.html')


def get_permission_for_action(action, model):
    """
    Вспомогательная функция для получения полного имени разрешения
    для заданного действия и модели.
    """
    app_label = model._meta.app_label
    permission_codename = get_permission_codename(action, model._meta)
    return f"{app_label}.{permission_codename}"

@login_required
@permission_required(get_permission_for_action('change', Product), login_url='/')
def update_product(request):
    return render(request, 'business_app/update_product.html')


@login_required
def profile(request):
    context = get_user_group_context(request.user)
    return render(request, 'business_app/profile.html')


@login_required
def update_profile(request):
    if request.method == 'POST':
        profile_form = UpdateProfileForm(request.POST, instance=request.user)
        password_form = PasswordChangeForm(user=request.user, data=request.POST)

        if profile_form.is_valid() and password_form.is_valid():
            profile_form.save()
            user = password_form.save()
            update_session_auth_hash(request, user)  # Обновляем сессию аутентификации

            messages.success(request, 'Ваш профиль был успешно обновлён!')
            logout(request)  # Логаут пользователя
            return redirect('authorization')  # Переадресация на страницу авторизации
    else:
        profile_form = UpdateProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)

    return render(request, 'business_app/update_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })


def logout_view(request):
    logger.info(f"User {request.user.username} logged out.")
    logout(request)
    return redirect(reverse('main_page'))


# @login_required
def purchase(request):
    # Проверка: авторизован ли пользователь
    if request.user.is_authenticated:
        # Проверка прав доступа: принадлежит ли пользователь к группе "customer"
        if request.user.groups.filter(name='customer').exists():
            # Если авторизован и имеет нужные права, отобразить страницу покупок
            return render(request, 'business_app/purchase.html')
        else:
            # Сообщение, если пользователь не имеет прав "customer"
            message = "У вас нет прав для просмотра этой страницы."
    else:
        # Сообщение для неавторизованных пользователей
        message = "Чтобы посмотреть покупки, пожалуйста, авторизуйтесь."

    # Если пользователь не авторизован или не имеет прав, показываем сообщение
    return render(request, 'business_app/purchase.html', {'message': message})

# @login_required
def sale(request):
    context = get_user_group_context(request.user)
    if context['is_salesman']:
        return render(request, 'business_app/sale.html', context)
    else:
        return redirect(reverse('main_page'))


@login_required
def profile(request):
    context = get_user_group_context(request.user)
    return render(request, 'business_app/profile.html')


def redirect_user_based_on_group(user):
    """Redirect user based on their group."""
    if user.groups.filter(name='customer').exists():
        return redirect(reverse('purchase'))
    elif user.groups.filter(name='salesman').exists():
        return redirect(reverse('sale'))
    else:
        return redirect(reverse('profile'))


# Обработчик 404 ошибки
def custom_404(request, _exception):
    # Проверка, авторизован ли пользователь
    if request.user.is_authenticated:
        # Проверка группы, к которой принадлежит пользователь
        if request.user.groups.filter(name='customer').exists():
            return render(request, 'business_app/purchase.html')
        elif request.user.groups.filter(name='salesman').exists():
            return render(request, 'business_app/sale.html')

    # Для неавторизованных пользователей или если пользователь не в указанных группах
    return render(request, 'business_app/page_404.html')