"""Modelos del bot CACEH.

Contract es el núcleo del producto: la constancia timestamped de que la
relación laboral existió. `data` guarda un snapshot de todos los extras del
miembro al momento de registrar (la "constancia" propiamente dicha), de modo
que el contrato queda probado aunque los extras cambien después.
"""
from django.db import models

from infrastructure.member.models import Member
from infrastructure.persistent_media.models import Media
from infrastructure.place.models import Account


class Contract(models.Model):
    TIPO_CHOICES = (
        ("planta", "De planta"),
        ("entrada_salida", "Entrada por salida"),
    )

    folio = models.CharField(max_length=30, unique=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CHOICES)
    trab_nombre = models.CharField(max_length=180)
    empl_nombre = models.CharField(max_length=180)
    data = models.JSONField(default=dict)
    pdf = models.ForeignKey(
        Media, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

    def __str__(self):
        return self.folio or f"Contrato sin folio (pk={self.pk})"

    def save(self, *args, **kwargs):
        # El folio deriva del pk y la fecha, que solo existen tras el INSERT:
        # se guarda una vez para obtenerlos y se reescribe solo el folio.
        super().save(*args, **kwargs)
        if not self.folio:
            fecha = self.created_at.strftime("%Y%m%d")
            self.folio = f"CACEH-{fecha}-{self.pk:05d}"
            super().save(update_fields=["folio"])
