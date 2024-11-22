import logging

import datetime
from datetime import timedelta

from django.db.models import F
from django.utils import timezone

# Импорты админки, авторизации и разграничения доступа
from django.contrib import messages
from django.contrib.auth import (authenticate, get_backends, get_permission_codename,
                                login, logout, update_session_auth_hash)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist

# Импорт для кастомной формы авторизации
from allauth.account.views import email
from .forms import CustomSignupForm, CustomLoginForm
from .forms import UpdateProfileForm

# Импорты рендеринга шаблонов
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseServerError, HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views import View

from .logger import log_error
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

# Импорты для управления отзывами
from .models import Review
from .forms import ReviewForm, ReplyForm


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

# def my_view(request):
#     """ Метод отображения страницы покупки, если пользователь авторизован. """
#     if request.user.is_authenticated:
#         context = get_user_group_context(request.user)
#         return render(request, 'business_app/purchase.html', context)
#     else:
#         return redirect('page_errors')


def redirect_user_based_on_group(user):
    """ Метод перенаправления пользователя на страницу, соответствующую группе допуска. """
    if user.groups.filter(name='customer').exists():
        return redirect('purchase')
    elif user.groups.filter(name='salesman').exists():
        return redirect('sale')
    else:
        return redirect('main_page')


def main_page(request):
    # Получаем все продукты из базы данных
    products_list = Product.objects.filter(is_active=True)

    # Настройка пагинации
    paginator = Paginator(products_list, 6)  # Показываем 6 товаров на странице
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
            user_email = form.cleaned_data.get('email')  # Используем 'email'
            password = form.cleaned_data.get('password')

            # Аутентификация пользователя по email и паролю
            user = authenticate(request, email=user_email, password=password)

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

""" Методы проверки принадлежности и разграничения прав"""

def is_in_group(group_name):
    """Функция для создания проверки принадлежности к группе."""
    def check(user):
        try:
            result = user.groups.filter(name=group_name).exists()
            logger.debug(f"Проверка принадлежности к группе '{group_name}' для пользователя {user.username}: {result}")
            return result
        except Exception as e:
            logger.error(f"Ошибка при проверке группы пользователя: {e}")
            return False
    return check

def order_belongs_to_user(view_func):
    """Декоратор для проверки, принадлежит ли заказ пользователю."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        try:
            if order_id is not None:
                order = get_object_or_404(Order, id=order_id)
                logger.debug(f"Заказ с ID {order_id} найден для пользователя {request.user.username}")
                if order.user != request.user:
                    logger.warning(f"Пользователь {request.user.username} попытался получить доступ к чужому заказу с ID {order_id}")
                    return HttpResponseForbidden("Вы не можете редактировать этот заказ.")
        except Exception as e:
            logger.error(f"Ошибка при проверке заказа: {e}")
            return HttpResponseServerError("Произошла внутренняя ошибка сервера.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def customer_required(view_func):
    """Декоратор для проверки авторизации и принадлежности к группе 'customer'."""
    @login_required(login_url='page_errors')
    @user_passes_test(is_in_group('customer'), login_url='page_errors', redirect_field_name=None)
    @order_belongs_to_user
    def _wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка в представлении {view_func.__name__}: {e}")
            return HttpResponseServerError("Произошла внутренняя ошибка сервера.")
    return _wrapped_view


def salesman_required(view_func):
    """Декоратор для проверки авторизации и принадлежности к группе 'salesman'."""
    @login_required(login_url='page_errors')
    @user_passes_test(is_in_group('salesman'), login_url='page_errors', redirect_field_name=None)
    def _wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка в представлении {view_func.__name__}: {e}")
            return HttpResponseServerError("Произошла внутренняя ошибка сервера.")
    return _wrapped_view


""" Методы для управления корзиной """


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
        cart[str(product_id)] = {
            'quantity': 1,
            'product_name': product.name,
            'price': float(product.price)  # Конвертация в float
        }

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
    try:
        cart = request.session.get('cart', {})
        items_with_products = []

        logger.debug(f"Обрабатываем корзину: {cart}")
        for product_id, item in cart.items():
            logger.debug(f"Обрабатывается product_id: {product_id}, item: {item}")
            if not product_id:
                logger.error(f"Продукт с пустым ID: {item}")
                continue  # Пропускаем некорректные элементы

            # Преобразуем ключ product_id в int и проверяем его
            try:
                product = get_object_or_404(Product, id=int(product_id))
            except ValueError:
                logger.error(f"Некорректный формат product_id: {product_id}")
                continue

            price = item.get('price', product.price)
            quantity = item['quantity']
            line_total = price * quantity

            items_with_products.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'line_total': line_total,
            })

        context = {
            'cart': items_with_products,
            'total_amount': sum(item['line_total'] for item in items_with_products),
            'cart_form': CartForm(),
        }
        return render(request, 'business_app/cart_detail.html', context)

    except Exception as e:
        logger.error(f"Ошибка при отображении корзины: {e}")
        return HttpResponseForbidden("Произошла ошибка при обработке корзины.")


def calculate_total_amount(order):
    return sum(item.product.price * item.quantity for item in order.orderitem_set.all())


@customer_required
def create_order(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        cart_data = request.POST.get('cart_data')

        logger.debug(f"Содержимое корзины перед созданием заказа: {cart}")
        logger.debug(f"Полученные данные корзины из формы: {cart_data}")

        if not cart:
            return redirect('cart_detail')

        cart_form = CartForm(request.POST)
        if cart_form.is_valid():
            order = Order.objects.create(
                user=request.user,
                phone=cart_form.cleaned_data['phone'],
                address=cart_form.cleaned_data['address'],
                comment=cart_form.cleaned_data.get('comment', ''),
                status=Order.STATUS_CONFIRMED,
                status_datetime=timezone.now()
            )

            for product_id, item in cart.items():
                try:
                    product_id = int(product_id)
                    product = get_object_or_404(Product, id=product_id)
                    OrderItem.objects.create(order=order, product=product, quantity=item['quantity'])
                except Exception as e:
                    logger.error(f"Ошибка обработки товара: {e}")

            request.session['cart'] = {}
            request.session.save()
            return redirect('purchase')
        else:
            logger.error(f"Форма недействительна: {cart_form.errors}")

            items_with_products = []
            for product_id, item in cart.items():
                product = get_object_or_404(Product, id=int(product_id))
                price = item.get('price', product.price)
                quantity = item['quantity']
                line_total = price * quantity
                items_with_products.append({
                    'product': product,
                    'quantity': quantity,
                    'price': price,
                    'line_total': line_total,
                })

            return render(request, 'business_app/cart_detail.html', {
                'cart': items_with_products,
                'total_amount': sum(item['line_total'] for item in items_with_products),
                'cart_form': cart_form
            })
    return redirect('cart_detail')


# Методы редактирования заказа

@customer_required
def edit_order(request, order_id):
    """
    Создает временный заказ для редактирования. Копирует товары из оригинального заказа и помещает их в корзину.
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

    return render(request, 'business_app/cart_detail.html', {'cart': cart, 'total_amount': total_amount})

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
    try:
        temporary_order = get_object_or_404(Order, id=order_id, user=request.user, status=Order.STATUS_PENDING)
        original_order = temporary_order.original_order

        logger.debug(f"Найден временный заказ {temporary_order.id} для пользователя {request.user.username}")

        # Начинаем транзакцию
        with transaction.atomic():
            # Обновляем оригинальный заказ
            original_order.orderitem_set.all().delete()
            logger.debug(f"Все позиции из оригинального заказа {original_order.id} удалены")

            cart = request.session.get('cart', {})
            for product_id, item in cart.items():
                product = get_object_or_404(Product, id=product_id)
                OrderItem.objects.create(order=original_order, product=product, quantity=item['quantity'])
                logger.debug(f"Добавлен продукт {product_id} в оригинальный заказ {original_order.id}")

            original_order.status = Order.STATUS_CONFIRMED
            original_order.save()
            logger.debug(f"Статус оригинального заказа {original_order.id} обновлен на {Order.STATUS_CONFIRMED}")

            # Удаляем временный заказ и очищаем корзину
            temporary_order.delete()
            logger.debug(f"Временный заказ {temporary_order.id} удален")

            if 'cart' in request.session:
                del request.session['cart']
                logger.debug(f"Корзина очищена для пользователя {request.user.username}")

        return redirect('purchase')

    except Exception as e:
        logger.error(f"Ошибка при подтверждении изменений заказа {order_id} для пользователя {request.user.username}: {e}")
        return HttpResponseForbidden("Произошла ошибка при обработке вашего запроса в представлении confirm_order_changes.")


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


@customer_required
def purchase(request):
    # Получаем заказы текущего пользователя
    orders = Order.objects.filter(user=request.user).prefetch_related('orderitem_set__product').order_by(
        '-status_datetime')

    # Разделяем заказы на текущие и исторические
    current_orders = orders.filter(status__in=[
        Order.STATUS_PENDING,
        Order.STATUS_CONFIRMED,
        Order.STATUS_DELIVERY
    ])

    historical_orders = orders.filter(status__in=[
        Order.STATUS_COMPLETED,
        Order.STATUS_CANCELED
    ])

    # Подготовка контекста для передачи в шаблон
    context = {
        'current_orders': current_orders,
        'historical_orders': historical_orders,
        'STATUS_PENDING': Order.STATUS_PENDING,
        'STATUS_CONFIRMED': Order.STATUS_CONFIRMED,
        'STATUS_DELIVERY': Order.STATUS_DELIVERY,
        'STATUS_COMPLETED': Order.STATUS_COMPLETED,
        'STATUS_CANCELED': Order.STATUS_CANCELED,
    }

    return render(request, 'business_app/purchase.html', context)

""" Методы работы с продавцами управления продуктами каталога и статистикой продаж """

def is_salesman (user):
    """Проверка, является ли пользователь членом группы 'salesman'."""
    try:
        result = user.groups.filter(name='salesman').exists()
        logger.debug(f"Проверка is_salesman для пользователя {user.username}: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при проверке группы пользователя: {e}")
        return False  # Здесь возврат False логичен, так как мы не можем подтвердить принадлежность к группе

# # @login_required
# def sale(request):
#     context = get_user_group_context(request.user)
#     if context['is_salesman']:
#         return render(request, 'business_app/sale.html', context)
#     else:
#         return redirect(reverse('main_page'))

@salesman_required
def sale(request):
    """
    Получение доступа к панели продавца,
    в которой есть возможность управлению продуктами, заказами, их мониторинга и анализа статистики.
    """
    context = get_user_group_context(request.user)
    return render(request, 'business_app/sale.html', context)


@salesman_required
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


@salesman_required
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


@salesman_required
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


@salesman_required
def toggle_product_status(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save()
    messages.success(request, f"Статус продукта '{product.name}' был успешно изменен.")
    return redirect('product_list')


""" Методы управления отзывами """


@login_required  # Добавляем декоратор для проверки аутентификации
def review(request, order_id):
    # Получаем информацию о группах пользователя
    context = get_user_group_context(request.user)

    # Проверяем, оставлял ли пользователь отзыв
    user_has_reviewed = Review.objects.filter(user=request.user, order_id=order_id).exists()

    if request.method == 'POST':
        if user_has_reviewed:
            messages.error(request, 'Вы уже оставили отзыв на этот заказ.')
            return redirect('review', order_id=order_id)

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.order_id = order_id
            review.save()
            messages.success(request, 'Отзыв успешно добавлен.')
            return redirect('review', order_id=order_id)
    else:
        form = ReviewForm()

    # Получаем все отзывы для данного заказа
    reviews = Review.objects.filter(order_id=order_id).select_related('user')

    # Обновляем контекст
    context.update({
        'reviews': reviews,
        'form': form,
        'order_id': order_id,
        'user_has_reviewed': user_has_reviewed,
    })

    return render(request, 'business_app/review.html', context)


@salesman_required
def reply_to_review(request, order_id):
    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        if review_id:
            target_review = get_object_or_404(Review, id=review_id)
            form = ReplyForm(request.POST)
            if form.is_valid():
                reply = form.save(commit=False)
                reply.review = target_review
                reply.save()
                return redirect('review', order_id=order_id)
            else:
                # Возвращает JSON с ошибками валидации
                return JsonResponse({'error': 'Ответ не прошел проверку.', 'form_errors': form.errors}, status=400)
        else:
            # Если review_id не передан
            return JsonResponse({'error': 'Не указан идентификатор отзыва.'}, status=400)
    return JsonResponse({'error': 'Метод не разрешен.'}, status=403)


@salesman_required
def delete_review(request, review_id):
    local_review = get_object_or_404(Review, id=review_id)
    local_review.delete()
    return redirect('review', order_id=local_review.order_id)


def all_reviews(request):
    reviews = Review.objects.all().select_related('user').order_by('-pub_date').annotate(user_first_name=F('user__first_name'))

    context = {
        'reviews': reviews
    }
    return render(request, 'business_app/all_reviews.html', context)


def handle_permission_denied_or_not_found(request, exception=None):
    """
    Обработчик для ошибок доступа (403) и отсутствующих страниц (404).
    """

    error_message = "Произошла ошибка"
    status_code = 500  # Определим переменную status_code, чтобы избежать ошибки, если исключение не обработано

    if exception:
        if isinstance(exception, PermissionDenied):
            error_message = "У вас нет прав для доступа к этой странице."
            status_code = 403
            log_error(f"Ошибка доступа (403): {str(exception)}")
        elif isinstance(exception, Http404):
            error_message = "Страница не найдена."
            status_code = 404
            log_error(f"Страница не найдена (404): {str(exception)}")
    # Удаляем обработку всех других исключений и логирование ошибки 500

    context = {'error_message': error_message}
    return render(request, 'business_app/page_errors.html', context, status=status_code)
