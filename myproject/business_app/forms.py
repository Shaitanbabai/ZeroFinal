import logging
from django import forms
from django.core.exceptions import ValidationError
from allauth.account.forms import SignupForm, LoginForm as AllauthLoginForm
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserChangeForm

# Настройка логгера
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
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.user_cache = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Проверка на существование пользователя с данным email
        if not User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с данным email не найден.")
        return email

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        self.user_cache = None

        if email and password:
            logger.debug(f"Attempting authentication for: {email}")
            # Проверьте, что self.request инициализирован корректно
            if self.request is None:
                logger.error("Request object is None in CustomLoginForm.clean()")
                raise ValueError("Request object is required")

            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                logger.warning("Authentication failed: Invalid email or password.")
                self.add_error('password', "Неправильный email или пароль.")
            else:
                logger.info(f"Authentication successful for: {email}")
                self.confirm_email_allowed(self.user_cache)
        else:
            logger.warning("Email or password not provided.")

        return super().clean(*args, **kwargs)

    def get_user(self):
        return self.user_cache

    def login(self, *args, **kwargs):
        return super(CustomLoginForm, self).login(*args, **kwargs)

    def confirm_email_allowed(self, user):
        if not user.is_active:
            raise ValidationError("Этот аккаунт неактивен.")


class UpdateProfileForm(UserChangeForm):
    password = None  # Убираем поле пароля из формы, т.к. оно будет отдельно

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']