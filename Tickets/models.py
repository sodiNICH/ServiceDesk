from django.db import models
from django.contrib.postgres.fields import ArrayField


class Tickets(models.Model):
    STATUS_CHOICES = (
        ("new", "Новый"),
        ("in_process", "В процессе"),
        ("closed", "Завершен"),
    )

    id_mails = ArrayField(models.PositiveIntegerField(default=0), blank=True)
    email = models.EmailField(null=True, blank=True)
    subject = models.CharField(max_length=255)
    bodies = ArrayField(models.TextField(verbose_name="Описание проблемы"), blank=True)
    messages_id = ArrayField(models.TextField(blank=True))
    status = models.CharField(
        max_length=11,
        choices=STATUS_CHOICES,
        default="new",
        verbose_name="Статус решения проблемы",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания обращения"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата обновления статуса"
    )

    def __str__(self):
        return f"{self.subject} - {self.status}"

    def save(self, *args, **kwargs):
        if self.status not in dict(self.STATUS_CHOICES):
            raise ValueError(f"Недопустимый статус: {self.status}")
        super().save(*args, **kwargs)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "обращение"
        verbose_name_plural = "Обращения"
