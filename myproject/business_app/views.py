import logging

import datetime
from datetime import timedelta
from django.utils import timezone

# Импорты админки, авторизации и разграничения доступа
from django.contrib import messages
from django.contrib.auth import (authenticate, get_backends, get_permission_codename,
                                login, logout, update_session_auth_hash)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

# Импорт для кастомной формы авторизации
from allauth.account.views import email
from .forms import CustomSignupForm, CustomLoginForm
from .forms import UpdateProfileForm

# Импорты рендеринга шаблонов
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views import View

# Импорты для создания и управления продуктом
from .models import Product
from .forms import CreateProductForm

# Импорты для управления формой заказа
# from django.views.decorators.http import require_POST
from django.db import transaction
from django.db import DatabaseError
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseForbidden
from functools import wraps
from .forms import CartForm
from .models import Order, OrderItem

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


""" Методы управления заказами """
def is_customer(user):
    """Проверка, является ли пользователь членом группы 'customer'."""
    return user.groups.filter(name='customer').exists()

def order_belongs_to_user(view_func):
    """Декоратор для проверки, принадлежит ли заказ пользователю."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        if order_id is not None:
            order = get_object_or_404(Order, id=order_id)
            if order.user != request.user:
                return HttpResponseForbidden("Вы не можете редактировать этот заказ.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def customer_required(view_func):
    """Объединенный декоратор для проверки авторизации и принадлежности к группе."""
    @login_required(login_url='page_errors')
    @user_passes_test(is_customer, login_url='page_errors', redirect_field_name=None)
    @order_belongs_to_user
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Методы для управления корзиной

@customer_required
def add_to_cart(request, product_id):
    """
    Добавляет товар в корзину.
    Если товар уже в корзине, увеличивает количество.
    """
    product = get_object_or_404(Product, id=product_id)

    # Используем сессию для временного хранения данных корзины
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {'quantity': 1, 'product_name': product.name, 'price': product.price}

    # Обновляем данные в сессии
    request.session['cart'] = cart

    return redirect('cart_detail')


@customer_required
def remove_from_cart(request, product_id):
    """
    Удаляет товар из корзины.
    """
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]

    request.session['cart'] = cart
    return redirect('cart_detail')


@customer_required
def clear_cart(request):
    """Очищает временные данные корзины из сессии."""
    if 'cart' in request.session:
        del request.session['cart']
    return redirect('cart_detail')


@customer_required
def cart_detail(request):
    """
    Отображает содержимое корзины и общую сумму.
    """
    cart = request.session.get('cart', {})
    total_amount = sum(item['price'] * item['quantity'] for item in cart.values())

    return render(request, 'cart_detail.html', {'cart': cart, 'total_amount': total_amount})


# Методы создания заказа и работы с сессией

@customer_required
def create_order(request):
    """
    Создает заказ на основе содержимого корзины.
    После создания очищает корзину.
    """
    if request.method == 'POST':
        # Создаем новый заказ на основе данных из сессии
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('cart_detail')

        order = Order.objects.create(user=request.user, status=Order.STATUS_CONFIRMED, status_datetime=timezone.now())
        for product_id, item in cart.items():
            product = get_object_or_404(Product, id=product_id)
            OrderItem.objects.create(order=order, product=product, quantity=item['quantity'])

        # После создания заказа очищаем временные данные корзины
        del request.session['cart']
        return redirect('purchase')

    return redirect('cart_detail')

# Методы редактирования заказа

@customer_required
def edit_order(request, order_id):
    """
    Создает временный заказ для редактирования.
    Копирует товары из оригинального заказа и помещает их в корзину.
    """
    original_order = get_object_or_404(Order, id=order_id, user=request.user)

    # Создаем временный заказ
    temporary_order, created = Order.objects.get_or_create(
        user=request.user,
        original_order=original_order,
        status=Order.STATUS_PENDING
    )

    if created:
        # Копируем товары из оригинального заказа в временный
        for item in original_order.orderitem_set.all():
            OrderItem.objects.create(order=temporary_order, product=item.product, quantity=item.quantity)

    # Переносим товары из временного заказа в сессию для редактирования
    cart = {}
    for item in temporary_order.orderitem_set.all():
        cart[str(item.product.id)] = {'quantity': item.quantity, 'product_name': item.product.name, 'price': item.product.price}
    request.session['cart'] = cart

    return redirect('edit_order_detail', order_id=temporary_order.id)

# Управление состоянием временного заказа.

@customer_required
def edit_order_detail(request, order_id):
    """
    Позволяет пользователю просмотреть и подтвердить изменения во временном заказе.
    """
    temporary_order = get_object_or_404(Order, id=order_id, user=request.user, status=Order.STATUS_PENDING)

    if request.method == 'POST':
        if 'confirm' in request.POST:
            return redirect('confirm_order_changes', order_id=temporary_order.id)
        elif 'cancel' in request.POST:
            temporary_order.delete()
            return redirect('purchase')

    # Получаем данные корзины из сессии для отображения
    cart = request.session.get('cart', {})
    total_amount = sum(item['price'] * item['quantity'] for item in cart.values())

    return render(request, 'cart_detail.html', {'cart': cart, 'total_amount': total_amount})

# Представление для проверки доступности продукта в корзине
# Требуется создать функционал для управления запасами и остатками.
# Сейчас просто предполагается, что все product_id в статусе active доступны для продажи.
# @login_required
# def check_product_availability(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     # Логика проверки доступности
#     is_available = product.stock > 0
#     return JsonResponse({'is_available': is_available})

@customer_required
def confirm_order_changes(request, order_id):
    """
    Подтверждает изменения во временном заказе и переносит их в оригинальный
    """
    temporary_order = get_object_or_404(Order, id=order_id, user=request.user, status=Order.STATUS_PENDING)
    original_order = temporary_order.original_order

    # Начинаем транзакцию
    with transaction.atomic():
        # Обновляем оригинальный заказ
        original_order.orderitem_set.all().delete()
        cart = request.session.get('cart', {})
        for product_id, item in cart.items():
            product = get_object_or_404(Product, id=product_id)
            OrderItem.objects.create(order=original_order, product=product, quantity=item['quantity'])

        original_order.status = Order.STATUS_CONFIRMED
        original_order.save()

        # Удаляем временный заказ и очищаем корзину
        temporary_order.delete()
        if 'cart' in request.session:
            del request.session['cart']

    return redirect('purchase')

@customer_required
def cancel_order(request, order_id):
    """
    Отменяет заказ
    """
    # Получаем заказ пользователя с определенным ID и проверяем его статус
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == Order.STATUS_CONFIRMED:
        # Начинаем транзакцию
        with transaction.atomic():
            order.status = Order.STATUS_CANCELED
            order.status_datetime = timezone.now()
            order.save()

    return redirect('purchase')

def calculate_total_amount(order):
    return sum(item.product.price * item.quantity for item in order.orderitem_set.all())


@customer_required
def purchase(request):
    """
    Отображает список заказов пользователя
    """
    # Получаем заказы пользователя и фильтруем по статусу
    pending_orders = Order.objects.filter(user=request.user, status=Order.STATUS_PENDING)
    confirmed_orders = Order.objects.filter(user=request.user, status=Order.STATUS_CONFIRMED)
    delivered_orders = Order.objects.filter(user=request.user, status=Order.STATUS_DELIVERY)
    canceled_orders = Order.objects.filter(user=request.user, status=Order.STATUS_CANCELED)
    completed_orders = Order.objects.filter(user=request.user, status=Order.STATUS_COMPLETED)

    return render(request, 'purchase.html', {
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'delivered_orders': delivered_orders,
        'canceled_orders': canceled_orders,
        'completed_orders': completed_orders
    })


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
        'is_customer': True,
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
