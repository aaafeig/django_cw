from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.mail import send_mail


class Recipient(models.Model):
    email = models.EmailField(unique=True)
    fullname = models.CharField(max_length=200, verbose_name="ФИО")
    comment = models.TextField(verbose_name="Комментарий")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipient",
        verbose_name="Владелец",
        blank=True,
    )

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "получатель"
        verbose_name_plural = "получатели"
        ordering = [
            "fullname",
        ]


class Message(models.Model):
    topic = models.CharField(max_length=200, verbose_name="Тема")
    content = models.TextField(verbose_name="Содержимое")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message",
        verbose_name="Владелец",
        blank=True,
    )

    def __str__(self):
        return self.topic

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"
        ordering = [
            "topic",
        ]


class MailingLog(models.Model):

    SUCCESS = "Успешно"
    FAILED = "Не успешно"

    STATUS_CHOICES = [
        (SUCCESS, "Успешно"),
        (FAILED, "Не успешно"),
    ]

    mailing = models.ForeignKey(
        "Mailings",
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="Рассылка",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name="Статус попытки"
    )
    error_message = models.TextField(
        blank=True, null=True, verbose_name="Сообщение об ошибке"
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата и время попытки"
    )
    server_response = models.TextField(
        blank=True, null=True, verbose_name="Ответ почтового сервера"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailing_logs",
        verbose_name="Владелец",
        blank=True,
    )

    class Meta:
        verbose_name = "попытка рассылки"
        verbose_name_plural = "попытки рассылок"
        ordering = [
            "attempt_time",
        ]

    def __str__(self):
        return f"Попытка {self.attempt_time} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.owner and self.mailing:
            pass
        super().save(*args, **kwargs)


class Mailings(models.Model):

    CREATED = "Создана"
    STARTED = "Запущена"
    FINISHED = "Завершена"

    STATUS_CHOICES = [
        (CREATED, "Создана"),
        (STARTED, "Запущена"),
        (FINISHED, "Завершена"),
    ]

    start_time = models.DateTimeField(
        null=False, blank=False, verbose_name="Дата и время начала отправки"
    )
    end_time = models.DateTimeField(
        null=False, blank=False, verbose_name="Дата и время окончания отправки"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=CREATED,
        verbose_name="Статус рассылки",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Сообщение",
    )
    recipients = models.ManyToManyField(
        Recipient, related_name="mailings", verbose_name="Получатели"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Владелец",
        blank=True,
    )
    manually_controlled = models.BooleanField(
        default=False, verbose_name="Ручное управление"
    )

    def __str__(self):
        return f"Дата: {self.start_time} Получатель:{self.recipients}"

    class Meta:
        verbose_name = "рассылка"
        verbose_name_plural = "рассылки"
        ordering = [
            "start_time",
        ]

    def update_status(self, save=True):
        if self.manually_controlled:
            return self.status

        now = timezone.now()

        if now < self.start_time:
            new_status = self.CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STARTED
        else:
            new_status = self.FINISHED

        if self.status != new_status:
            self.status = new_status
            if save:
                self.save(update_fields=["status"])

        return new_status

    def can_send_now(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def send_mailing(self):
        if not self.can_send_now():
            return 0, 0, "Время не в диапазоне"

        sent = 0
        total = self.recipients.count()

        if total == 0:
            return 0, 0, "Нет получателей"

        for recipient in self.recipients.all():
            try:
                send_mail(
                    subject=self.message.topic,
                    message=self.message.content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )

                MailingLog.objects.create(
                    mailing=self,
                    status=MailingLog.SUCCESS,
                    server_response="Письмо отправлено успешно",
                    owner=self.owner,
                )
                sent += 1

            except Exception as e:
                MailingLog.objects.create(
                    mailing=self,
                    status=MailingLog.FAILED,
                    server_response=str(e),
                    owner=self.owner,
                )

        return sent, total, f"Отправлено {sent} из {total}"
