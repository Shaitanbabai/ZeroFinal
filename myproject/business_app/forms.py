from django import forms
from django.core.exceptions import ValidationError
from allauth.account.forms import SignupForm, LoginForm as AllauthLoginForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from .models import Order
import logging

logger = logging.getLogger(__name__)


# Получаем модель пользователя, которая используется в проекте
User = get_user_model()

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


class UpdateProfileForm(UserChangeForm):
    password = None  # Убираем поле пароля из формы, т.к. оно будет отдельно

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['product', 'phone', 'address', 'comment']
