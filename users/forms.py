from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Введите email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email


class CustomAuthenticationForm(AuthenticationForm):
    pass


class CustomPasswordResetForm(PasswordResetForm):
    pass


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(help_text="Введите новый пароль")
    new_password2 = forms.CharField(help_text="Подтвердите новый пароль")


class ProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ["username"]
