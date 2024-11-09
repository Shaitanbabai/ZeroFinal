
import logging

from django.contrib import messages
from django.contrib.auth import (
    authenticate, get_backends, get_permission_codename, login, logout, update_session_auth_hash
)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views import View

from allauth.account.views import email

from .forms import CustomSignupForm, CustomLoginForm
from .forms import UpdateProfileForm

from .models import Product
from .forms import CreateProductForm

from .models import Order
from .forms import OrderForm, OrderItemFormSet


# Настройка логгера
logger = logging.getLogger(__name__)

""" Блок классов управляющий авторизацией и регистрацией."""

def get_user_group_context(user):
    """ Метод определения группы пользователя. """
    group_names = user.groups.values_list('name', flat=True)
    context = {
        'is_customer': 'customer' in group_names,
        'is_salesman': 'salesman' in group_names
    }
    return context


def redirect_user_based_on_group(user):
    """    Метод перенаправления пользователя на страницу, соответствующую группе допуска.
    Если пользователь не авторизован, происходит перенаправление на главную страницу.
    """
    if user.groups.filter(name='customer').exists():
        return redirect('purchase')
    elif user.groups.filter(name='salesman').exists():
        return redirect('sale')
    else:
        return redirect('main_page')


def main_page(request):
    # Получаем все продукты из базы данных
    products_list = Product.objects.all()

    # Настройка пагинации
    paginator = Paginator(products_list, 10)  # Показываем 10 товаров на странице
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    # Передаем продукты в контекст для шаблона
    return render(request, 'business_app/main_page.html', {'products': products})


class AuthorizationView(View):
    """    Метод авторизации пользователя.
    Если пользователь уже авторизован, происходит перенаправление на соответствующую страницу.
    Происходит валидация логина и пароля. Методы валидации описаны в forms.py и settings.py
    """
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
    """    Метод регистрации пользователя.
    Если пользователь уже авторизован, происходит перенаправление на соответствующую страницу.
    Происходит валидация полей формы. Методы валидации описаны в forms.py и settings.py
    Используется бэкенд Django и Allauth для аутентификации пользователя.
    """
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

def get_permission_for_action(action, model):
    """ Вспомогательная функция для получения полного имени разрешения для заданного действия и модели. """
    app_label = model._meta.app_label
    permission_codename = get_permission_codename(action, model._meta)
    return f"{app_label}.{permission_codename}"


""" Методы управления профилем пользователя """

@login_required(login_url='page_errors')
def profile(request):
    """ Вспомогательная функция для получения контекста групп пользователя """
    context = get_user_group_context(request.user)
    return render(request, 'business_app/profile.html', context)


@login_required(login_url='page_errors')
def update_profile(request):
    """ Вспомогательная функция для обновления профиля пользователя """
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

    return render(request, 'business_app/update_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })


def logout_view(request):
    """ Вспомогательные функции для выхода пользователя """
    logger.info(f"User {request.user.username} logged out.")
    logout(request)
    return redirect(reverse('main_page'))


""" Методы создания и обновления заказа для пользователей группы 'customer' """

def is_customer(user):
    """Проверка, является ли пользователь членом группы 'customer'."""
    return user.groups.filter(name='customer').exists()


@login_required(login_url='page_errors')
@user_passes_test(is_customer, login_url='page_errors', redirect_field_name=None)
def create_order(request):
    """
    Метод создания заказа. При создании заказа происходит валидация формы и формы с выбором продуктов.
    Если все проверки прошли успешно, происходит сохранение данных в базе данных.
    """
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            for form_item in formset:
                order_item = form_item.save(commit=False)
                order_item.order = order
                order_item.save()

            return redirect('purchase')  # Перенаправление на страницу покупок со статусом заказов

    else:
        form = OrderForm()
        formset = OrderItemFormSet()

    # Здесь вы можете добавить логику для отображения корзины пользователя
    # Например, получение текущих товаров в корзине из сессии или базы данных

    return render(request, 'business_app/order_form.html', {
        'form': form,
        'formset': formset,
    })


@login_required(login_url='page_errors')
@user_passes_test(is_customer, login_url='page_errors', redirect_field_name=None)
def purchase(request):
    """Получение статуса текущего заказа пользователя и его истории заказов. """
    current_order = Order.objects.filter(user=request.user, status='confirmed').first()
    completed_orders = Order.objects.filter(user=request.user, status='completed')
    canceled_orders = Order.objects.filter(user=request.user, status='canceled')

    context = {
        'current_order': current_order,
        'completed_orders': completed_orders,
        'canceled_orders': canceled_orders,
    }

    return render(request, 'business_app/purchase.html', context)


""" Методы работы с продавцами управления продуктами каталога и статистикой продаж """

def is_salesman (user):
    """Проверка, является ли пользователь членом группы 'salesman'."""
    return user.groups.filter(name='salesman').exists()

# # @login_required
# def sale(request):
#     context = get_user_group_context(request.user)
#     if context['is_salesman']:
#         return render(request, 'business_app/sale.html', context)
#     else:
#         return redirect(reverse('main_page'))

@login_required(login_url='page_errors')
@user_passes_test(is_salesman, login_url='page_errors', redirect_field_name=None)
def sale(request):
    """
    Получение доступа к панели продавца,
    в которой есть возможность управлению продуктами, заказами, их мониторинга и анализа статистики.
    """
    context = get_user_group_context(request.user)
    return render(request, 'business_app/sale.html', context)


@login_required(login_url='page_errors')
@user_passes_test(is_salesman, login_url='page_errors', redirect_field_name=None)
def product_list(request):
    """
    Метод отображения списка продуктов. В качестве параметра передается список продуктов.
    """
    products = Product.objects.all()

    # Фильтрация
    name_contains = request.GET.get('name_contains')
    if name_contains:
        products = products.filter(name__icontains=name_contains)
    description_contains = request.GET.get('description_contains')
    if description_contains:
        products = products.filter(description__icontains=description_contains)
    price_min = request.GET.get('price_min')
    if price_min:
        products = products.filter(price__gte=price_min)
    price_max = request.GET.get('price_max')
    if price_max:
        products = products.filter(price__lte=price_max)
    is_active = request.GET.get('is_active')
    if is_active in ['True', 'False']:
        products = products.filter(is_active=(is_active == 'True'))

    # Сортировка
    sort = request.GET.get('sort')
    if sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')
    elif sort == 'description_asc':
        products = products.order_by('description')
    elif sort == 'description_desc':
        products = products.order_by('-description')
    elif sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')

    return render(request, 'business_app/product_list.html', {'products': products, 'request': request})


# @login_required(login_url='page_errors')
# @user_passes_test(is_salesman, login_url='page_errors', redirect_field_name=None)
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Инициализируем контекст
    context = {
        'product': product,
        'is_customer': False,
        'is_salesman': False,
    }

    # Если пользователь авторизован, добавляем информацию о его группе
    if request.user.is_authenticated:
        context.update(get_user_group_context(request.user))

    return render(request, 'business_app/product_detail.html', context)


@login_required(login_url='page_errors')
@user_passes_test(is_salesman, login_url='page_errors', redirect_field_name=None)
def create_product(request):
    if request.method == "POST":
        form = CreateProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            if Product.objects.filter(image=product.image.path).exists():
                messages.error(request, f"Это изображение уже выбрано для {Product.objects.get(image=product.image.path).name}.")
            else:
                product.save()
                messages.success(request, "Продукт успешно создан.")
                return redirect('product_detail', product_id=product.id)
    else:
        form = CreateProductForm()
    return render(request,'business_app/create_product.html', {'form': form})


@login_required(login_url='page_errors')
@user_passes_test(is_salesman, login_url='page_errors', redirect_field_name=None)
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        form = CreateProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            new_image_path = form.cleaned_data['image'].path
            if new_image_path != product.image.path and Product.objects.filter(image=new_image_path).exists():
                messages.error(request, f"Это изображение уже выбрано для {Product.objects.get(image=new_image_path).name}.")
            else:
                form.save()
                messages.success(request, "Продукт успешно обновлён.")
                return redirect('product_detail', product_id=product.id)
    else:
        form = CreateProductForm(instance=product)
    return render(request, 'business_app/update_product.html', {'form': form, 'product': product})


@login_required(login_url='page_errors')
@user_passes_test(is_salesman, login_url='page_errors', redirect_field_name=None)
def toggle_product_status(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save()
    messages.success(request, f"Статус продукта '{product.name}' был успешно изменен.")
    return redirect('product_list')


# @login_required(login_url='page_errors')
# @permission_required(get_permission_for_action('change', Product), login_url='page_errors', raise_exception=True)
# def update_product(request):
#     return render(request, 'business_app/update_product.html')
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
