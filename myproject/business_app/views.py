from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.views import View
from django.urls import reverse
from .forms import RegistrationForm, LoginForm
import logging


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
        form = LoginForm()
        return render(request, 'business_app/authorization.html', {'form': form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info(f"User {user.username} logged in.")
            return redirect_user_based_on_group(user)
        else:
            context = {'form': form, 'errors': form.errors}
            return render(request, 'business_app/authorization.html', context)

@login_required
def purchase(request):
    context = get_user_group_context(request.user)
    if context['is_customer']:
        return render(request, 'business_app/purchase.html', context)
    else:
        return redirect(reverse('main_page'))

@login_required
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

class RegistrationView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'business_app/registration.html', {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            customer_group = Group.objects.get(name='customer')
            user.groups.add(customer_group)
            login(request, user)
            logger.info(f"New user {user.username} registered and logged in.")
            return redirect(reverse('purchase'))
        else:
            return render(request, 'business_app/registration.html', {'form': form, 'errors': form.errors})

def logout_view(request):
    logger.info(f"User {request.user.username} logged out.")
    logout(request)
    return redirect(reverse('main_page'))

def redirect_user_based_on_group(user):
    """Redirect user based on their group."""
    if user.groups.filter(name='customer').exists():
        return redirect(reverse('main_page'))
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