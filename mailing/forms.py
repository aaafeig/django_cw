from django import forms
from django.utils import timezone
from .models import Recipient, Message, Mailings


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ["email", "fullname", "comment"]

    def __init__(self, *args, **kwargs):
        super(RecipientForm, self).__init__(*args, **kwargs)

        self.fields["email"].widget.attrs.update({"class": "form-control", "placeholder": "Введите email получателя"})

        self.fields["fullname"].widget.attrs.update({"class": "form-control", "placeholder": "Введите ФИО получателя"})

        self.fields["comment"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Введите текст для получателя"}
        )


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["topic", "content"]

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)

        self.fields["topic"].widget.attrs.update({"class": "form-control", "placeholder": "Введите тему письма"})

        self.fields["content"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Введите содержимое письма"}
        )


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailings
        fields = ["start_time", "end_time", "message", "recipients"]

        now = timezone.localtime(timezone.now())
        min_datetime = now.strftime("%Y-%m-%dT%H:%M")

        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "min": min_datetime,
                    "placeholder": "Введите дату и время начала отправки рассылки",
                }
            ),
            "end_time": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "placeholder": "Введите дату и время окончания отправки рассылки",
                }
            ),
            "message": forms.Select(
                attrs={
                    "class": "form-control",
                    "placeholder": "Выберите сообщение для получателя (-ей)",
                }
            ),
            "recipients": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields["message"].queryset = Message.objects.filter(owner=self.user)

            self.fields["recipients"].queryset = Recipient.objects.filter(owner=self.user)

    def clean_start_time(self):
        start_time = self.cleaned_data.get("start_time")

        if start_time < timezone.now() - timezone.timedelta(seconds=59):
            raise forms.ValidationError("Дата и время начала не могут быть в прошлом.")

        return start_time

    def clean_end_time(self):
        end_time = self.cleaned_data.get("end_time")
        start_time = self.cleaned_data.get("start_time")

        if end_time is None:
            raise forms.ValidationError("Укажите дату и время окончания рассылки.")

        if start_time is None:
            return end_time

        if start_time >= end_time:
            raise forms.ValidationError("Дата и время окончания должны быть позже даты и времени начала.")

        return end_time