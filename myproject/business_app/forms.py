from django import forms
from django.core.exceptions import ValidationError
from allauth.account.forms import SignupForm, LoginForm as AllauthLoginForm
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

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

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        if email and password:
            print(f"Attempting authentication for: {email}")
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                print("Authentication failed: Invalid email or password.")
                self.add_error('password', "Неправильный email или пароль.")
            else:
                print(f"Authentication successful for: {email}")
                self.confirm_email_allowed(self.user_cache)
        return self.cleaned_data

    def get_user(self):
        return self.user_cache

    @staticmethod
    def confirm_email_allowed(user):
        if not user.is_active:
            raise ValidationError("Этот аккаунт неактивен.")
