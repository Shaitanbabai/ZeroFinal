from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, help_text='Обязательное поле.')
    last_name = forms.CharField(max_length=50, required=True, help_text='Обязательное поле.')
    email = forms.EmailField(max_length=50, required=True, help_text='Обязательное поле. Введите действительный адрес электронной почты.')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с данным email уже зарегистрирован.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Email', widget=forms.EmailInput(attrs={'autofocus': True}))

    class Meta:
        model = User
        fields = ('username', 'password')
