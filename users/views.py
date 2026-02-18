from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, UpdateView
from django.contrib.auth import login
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView

from users.forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    ProfileUpdateForm,
)
from users.models import CustomUser


class RegisterView(CreateView):
    template_name = "users/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save()

        token = get_random_string(length=32)
        user.verification_token = token
        user.verification_token_created = timezone.now()
        user.save()

        self.send_verification_email(user)

        messages.success(
            self.request,
            "Регистрация прошла успешна! Проверьте email для подтверждения.",
        )

        return redirect(self.success_url)

    def send_verification_email(self, user):
        verification_url = f"http://{self.request.get_host()}/users/verify/{user.id}/{user.verification_token}/"

        subject = "Подтвердите ваш email"
        message = f"""
        Привет, {user.username}!
        Для подтверждения вашего email перейдите по ссылке:
        {verification_url}

        Ссылка будет действительна 24 часа.
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        try:
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            print(f"Ошибка отправки email: {e}")


class LoginView(FormView):
    template_name = "users/login.html"
    form_class = CustomAuthenticationForm
    success_url = reverse_lazy("mailing:home")

    def form_valid(self, form):
        user = form.get_user()

        if not user.email_verified:
            messages.error(
                self.request,
                "Подтвердите ваш email для входа в систему. "
                "Проверьте вашу почту или запросите новое письмо.",
            )
            return redirect("users:login")

        login(self.request, user)
        messages.success(self.request, f"Добро пожаловать, {user.username}!")

        return super().form_valid(form)


def verify_email_view(request, user_id, token):
    user = get_object_or_404(CustomUser, id=user_id)

    if user.verification_token == token:
        user.email_verified = True
        user.verification_token = None
        user.verification_token_created = None
        user.save()

        messages.success(request, "Email подтвержден! Теперь вы можете войти.")
        return redirect("users:login")
    else:
        messages.error(request, "Неверная ссылка подтверждения.")
        return redirect("users:register")


class CustomPasswordResetView(PasswordResetView):
    template_name = "users/password_reset.html"
    success_url = reverse_lazy("users:password_reset_done")
    form_class = CustomPasswordResetForm
    email_template_name = "users/password_reset_email.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:login")
    form_class = CustomSetPasswordForm


class ProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = "users/profile.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Никнейм обновлен!")
        return super().form_valid(form)
