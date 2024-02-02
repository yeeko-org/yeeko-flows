from django.db import models
from django.db.models import JSONField

from infrastructure.service.models import Platform


def default_params():
    return {}


class Space(models.Model):

    title = models.CharField(max_length=180)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    bot_name = models.CharField(
        max_length=40, blank=True, null=True, default="Xico"
    )
    image = models.ImageField(upload_to='spaces', blank=True, null=True)
    test = models.BooleanField(default=False)
    params = JSONField(
        blank=True, null=True, default=default_params
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Espacios (Páginas)"
        verbose_name = "Espacio (Página)"


class Account(models.Model):
    pid = models.CharField(max_length=191, primary_key=True)
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    title = models.CharField(max_length=180, blank=True, null=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    config = JSONField(blank=True, null=True, default=default_params)
    active = models.BooleanField(default=True)
    init_text_response = models.BooleanField(default=True)
    text_response = models.BooleanField(default=True)
    payload_response = models.BooleanField(default=True)
    notif_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.space} - {self.platform}"

    class Meta:
        verbose_name_plural = "Cuentas por plataforma"
        verbose_name = "Cuenta por plataforma"
