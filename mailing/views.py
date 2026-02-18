from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, DeleteView, ListView
from django.views.generic.edit import CreateView, UpdateView
from django.utils import timezone
from mailing.mixins import ManagerAccessMixin
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from mailing.forms import RecipientForm, MessageForm, MailingForm
from mailing.models import Recipient, Message, Mailings, MailingLog


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = Recipient
    form_class = RecipientForm
    title = "Добавление получателя"
    template_name = "mailing/recipient_form.html"
    success_url = reverse_lazy("mailing:recipient_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class RecipientListView(LoginRequiredMixin, ManagerAccessMixin, ListView):
    model = Recipient
    template_name = "mailing/recipients_list.html"
    context_object_name = "recipients"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Manager").exists():
            cache_key = "recipients_all"
            queryset = cache.get(cache_key)

            if not queryset:
                queryset = Recipient.objects.all()
                cache.set(cache_key, queryset, 60 * 10)
        else:
            cache_key = f"recipients_user_{self.request.user.id}"
            queryset = cache.get(cache_key)

            if not queryset:
                queryset = Recipient.objects.filter(owner=self.request.user)
                cache.set(cache_key, queryset, 60 * 10)

        return queryset


class RecipientDetailView(LoginRequiredMixin, DetailView):
    model = Recipient
    template_name = "mailing/recipient_detail.html"
    context_object_name = "recipient"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Manager").exists():
            return Recipient.objects.all()
        return Recipient.objects.filter(owner=self.request.user)


class RecipientUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipient
    form_class = RecipientForm
    title = "Редактирование получателя"
    template_name = "mailing/recipient_form.html"
    success_url = reverse_lazy("mailing:recipient_list")

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


@method_decorator(cache_page(60 * 5), name="dispatch")
class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    model = Recipient
    template_name = "mailing/recipient_confirm_delete.html"
    success_url = reverse_lazy("mailing:recipient_list")

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


# Message
class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    title = "Добавление письма"
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageListView(LoginRequiredMixin, ManagerAccessMixin, ListView):
    model = Message
    template_name = "mailing/messages_list.html"
    context_object_name = "messages"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Manager").exists():
            cache_key = "messages_all"
            queryset = cache.get(cache_key)

            if not queryset:
                queryset = Message.objects.all()
                cache.set(cache_key, queryset, 60 * 10)
        else:
            cache_key = f"messages_user_{self.request.user.id}"
            queryset = cache.get(cache_key)

            if not queryset:
                queryset = Message.objects.filter(owner=self.request.user)
                cache.set(cache_key, queryset, 60 * 10)

        return queryset


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = "mailing/message_detail.html"
    context_object_name = "message"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Manager").exists():
            return Message.objects.all()
        return Message.objects.filter(owner=self.request.user)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    title = "Редактирование письма"
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


@method_decorator(cache_page(60 * 5), name="dispatch")
class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


# Mailing
class MailingsCreateView(LoginRequiredMixin, CreateView):
    model = Mailings
    form_class = MailingForm
    title = "Создание рассылки"
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailings_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        self.object.update_status()
        return response


class MailingsListView(LoginRequiredMixin, ManagerAccessMixin, ListView):
    model = Mailings
    template_name = "mailing/mailings_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Manager").exists():
            cache_key = "mailings_all"
        else:
            cache_key = f"mailings_user_{self.request.user.id}"

        queryset = cache.get(cache_key)

        if not queryset:
            if self.request.user.groups.filter(name="Manager").exists():
                queryset = Mailings.objects.all()
            else:
                queryset = Mailings.objects.filter(owner=self.request.user)

            for mailing in queryset:
                mailing.update_status()

            cache.set(cache_key, queryset, 60 * 5)

        return queryset


class MailingsDetailView(LoginRequiredMixin, DetailView):
    model = Mailings
    template_name = "mailing/mailing_detail.html"
    context_object_name = "mailing"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Manager").exists():
            return Mailings.objects.all()
        return Mailings.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_manager"] = self.request.user.groups.filter(name="Manager").exists()
        context["is_owner"] = self.request.user == self.object.owner
        return context

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingsUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailings
    form_class = MailingForm
    title = "Редактирование рассылки"
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailings_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_queryset(self):
        return Mailings.objects.filter(owner=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.update_status()
        return response


@method_decorator(cache_page(60 * 5), name="dispatch")
class MailingsDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailings
    template_name = "mailing/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailings_list")

    def get_queryset(self):
        return Mailings.objects.filter(owner=self.request.user)


# MailingLog
class SendMailingView(LoginRequiredMixin, View):
    def post(self, request, pk):
        mailing = get_object_or_404(Mailings, pk=pk, owner=request.user)

        mailing.update_status()
        if mailing.status != mailing.STARTED:
            messages.error(request, "Можно отправлять только активные рассылки")
            return redirect("mailing:mailing_detail", pk=pk)

        sent, total, message = mailing.send_mailing()

        if sent > 0:
            messages.success(request, message)
        else:
            messages.warning(request, message)

        return redirect("mailing:mailing_detail", pk=pk)


# HomePage
def home_view(request):
    now = timezone.now()

    is_manager = False
    if request.user.is_authenticated:
        is_manager = request.user.groups.filter(name="Manager").exists()

    total_mailings = Mailings.objects.count()
    active_mailings = Mailings.objects.filter(
        status=Mailings.STARTED, start_time__lte=now, end_time__gte=now
    ).count()
    unique_recipients = Recipient.objects.distinct().count()

    context = {
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "unique_recipients": unique_recipients,
        "is_manager": is_manager,
    }

    return render(request, "mailing/home.html", context)


# Statistic
@login_required
@cache_page(60 * 3)
def user_statistics_view(request):
    user = request.user

    user_mailings = Mailings.objects.filter(owner=user)

    total_mailings = user_mailings.count()
    active_mailings = user_mailings.filter(status=Mailings.STARTED).count()
    finished_mailings = user_mailings.filter(status=Mailings.FINISHED).count()

    user_logs = MailingLog.objects.filter(owner=user)
    total_attempts = user_logs.count()
    successful_attempts = user_logs.filter(status=MailingLog.SUCCESS).count()
    failed_attempts = user_logs.filter(status=MailingLog.FAILED).count()

    total_messages_sent = user_logs.filter(status=MailingLog.SUCCESS).count()

    context = {
        "user": user,
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "finished_mailings": finished_mailings,
        "total_attempts": total_attempts,
        "successful_attempts": successful_attempts,
        "failed_attempts": failed_attempts,
        "total_messages_sent": total_messages_sent,
    }

    return render(request, "mailing/statistics.html", context)


# Manager
@login_required
def toggle_mailing_active(request, pk):
    if not request.user.groups.filter(name="Manager").exists():
        messages.error(request, "Доступ только для менеджеров")
        return redirect("mailing:home")

    mailing = get_object_or_404(Mailings, pk=pk)

    mailing.manually_controlled = True

    if mailing.status == Mailings.STARTED:
        mailing.status = Mailings.CREATED
        action = "отключена"
    elif mailing.status == Mailings.CREATED:
        mailing.status = Mailings.STARTED
        action = "включена"
    else:
        messages.error(request, "Нельзя изменить статус завершенной рассылки")
        return redirect("mailing:mailing_detail", pk=pk)

    mailing.save()

    messages.success(request, f"Рассылка {action}")
    return redirect("mailing:mailing_detail", pk=pk)


@login_required
def user_list_view(request):
    if not request.user.groups.filter(name="Manager").exists():
        messages.error(request, "Доступ только для менеджеров")
        return redirect("mailing:home")

    from django.contrib.auth import get_user_model

    User = get_user_model()

    users = User.objects.filter(is_staff=False).order_by("-date_joined")
    return render(request, "mailing/user_list.html", {"users": users})


@login_required
def toggle_user_active(request, pk):
    if not request.user.groups.filter(name="Manager").exists():
        messages.error(request, "Доступ только для менеджеров")
        return redirect("mailing:home")

    from django.contrib.auth import get_user_model

    User = get_user_model()

    user = get_object_or_404(User, pk=pk)

    if user == request.user:
        messages.error(request, "Нельзя заблокировать самого себя")
        return redirect("mailing:user_list")

    user.is_active = not user.is_active
    user.save()

    action = "разблокирован" if user.is_active else "заблокирован"
    messages.success(request, f"Пользователь {user.username} {action}")

    return redirect("mailing:user_list")
