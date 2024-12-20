from django import forms
from django.core.exceptions import ValidationError
from allauth.account.forms import SignupForm, LoginForm as AllauthLoginForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from django.core.validators import RegexValidator
from .models import Review, Reply
# from django.forms import inlineformset_factory
from .models import Order  # OrderItem
from .models import Product
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Получаем модель пользователя, которая используется в проекте
User = get_user_model()

""" Блок классов для регистрации и авторизации.
Класс CustomSignupForm используется для регистрации нового пользователя. 
При регистрации нового пользователя, происходит сохранение данных пользователя в базе данных, 
создание пользователя в системе, создание группы пользователя.

"""

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        help_text='Обязательное поле.',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваше имя', 'id': 'id_first_name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        help_text='Обязательное поле.',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваша фамилия', 'id': 'id_last_name'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Проверка на уникальность email
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с данным email уже зарегистрирован.")
        return email

    def save(self, request):
        # Вызов родительского метода save и добавление дополнительных данных
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.username = user.email  # Установите username равным email
        user.save()
        return user


"""
Класс CustomLoginForm используется для авторизации пользователя. 
При авторизации пользователя, происходит проверка логина и пароля.
"""
class CustomLoginForm(AllauthLoginForm):
    def clean(self):
        # Вызовем базовый clean() для стандартной валидации
        super().clean()

        # Дополнительная проверка: наличие полей login и password
        if not self.cleaned_data.get("login") or not self.cleaned_data.get("password"):
            raise ValidationError("Пожалуйста, заполните оба поля.")

        # Логирование успешной валидации
        logger.info(f"Authentication attempt for user: {self.cleaned_data.get('login')}")

        return self.cleaned_data


"""
Класс UpdateProfileForm используется для обновления профиля пользователя. 
При обновлении профиля пользователя, происходит проверка пароля.
"""
class UpdateProfileForm(UserChangeForm):
    password = None  # Убираем поле пароля из формы, т.к. оно будет отдельно

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']


"""
Класс CreateProductForm используется для создания продукта. 
Задаются параметры, которые будут использоваться в форме и структура таблицы с продуктами
"""
class CreateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        try:
            super(CreateProductForm, self).__init__(*args, **kwargs)
            for field_name, field in self.fields.items():
                field.required = True
                logger.debug(f"Поле '{field_name}' установлено как обязательное.")
        except Exception as e:
            logger.error(f"Ошибка при инициализации формы: {e}")
            raise  # Поднимаем исключение дальше, если нужно


"""
Класс OrderForm используется для создания заказа. 
Задаются параметры, которые будут использоваться в форме и структура таблицы с заказами
"""
class CartForm(forms.ModelForm):
    phone = forms.CharField(
        label='Телефон получателя',
        widget=forms.TextInput(attrs={
            'placeholder': '+71234567890',
            'required': True
        }),
        validators=[RegexValidator(regex=r'^\+?\d{10,15}$', message='Введите корректный номер телефона.')]
    )
    address = forms.CharField(
        label='Адрес доставки',
        widget=forms.Textarea(attrs={
            'maxlength': 120,
            'placeholder': 'Город, Улица, Дом, Подъезд, Квартира/Офис',
            'required': True
        })
    )
    comment = forms.CharField(
        label='Комментарий',
        widget=forms.Textarea(attrs={
            'maxlength': 120,
            'placeholder': 'Комментарии к заказу для магазина, курьера или получателя',
            'required': False
        }),
        required=False
    )
    telegram_key = forms.CharField(
        label='Ключ Telegram',
        widget=forms.TextInput(attrs={
            'maxlength': 100,
            'placeholder': 'Введите ваше имя или имя получателя в Telegram, если хотите отслеживать заказ в боте',
            'required': False
        }),
        required=False
    )

    class Meta:
        model = Order
        fields = ['phone', 'address', 'comment', 'telegram_key']

    def clean_telegram_key(self):
        telegram_key = self.cleaned_data.get('telegram_key')
        if telegram_key and not telegram_key.startswith('@'):
            raise forms.ValidationError("Имя в Telegram  должно начинаться с @")
        return telegram_key


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['content', 'rating']

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']