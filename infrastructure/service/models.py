from pprint import pprint
import traceback
from typing import Optional
from django.db import models
from django.db.models import JSONField

from utilities.json_compatible import ensure_json_compatible

WAY_CHOICES = (
    ('in', 'entrada'),
    ('out', 'salida'),
    ('inout', 'inout'),
)

GROUP_TYPES = (
    ('interactive', 'Interactivo'),  # Mensaje con botones
    ('text', 'Texto escrito'),
    ('reply_button', 'Botón de respuesta'),  # Incluye simulación de botones
    ('media', 'Media'),
    ('event', 'Eventos y Reacciones'),
    ('special', 'Especial'),
    ('references', 'Referencias'),
    ('other', 'Otros'),
)


def default_dict():
    return {}


class Platform(models.Model):
    name = models.CharField(
        max_length=60, primary_key=True, verbose_name="Nombre clave (fijo)"
    )
    public_name = models.CharField(
        max_length=120, blank=True, null=True, verbose_name="Nombre público"
    )
    description = models.TextField(blank=True, null=True)
    config = JSONField(
        default=default_dict, blank=True,
        verbose_name="Configuración adicional"
    )
    with_users = models.BooleanField(
        default=True, verbose_name="Tiene usuarios"
    )
    id_field = models.CharField(
        max_length=120, blank=True, null=True, verbose_name="Campo de id"
    )
    internal = models.BooleanField(
        default=False, verbose_name="Es de Yeeko"
    )
    color = models.CharField(max_length=30, blank=True, null=True)
    icon = models.CharField(max_length=30, blank=True, null=True)
    image = models.ImageField(
        blank=True, null=True, upload_to='platform'
    )
    config_by_member = models.BooleanField(
        default=False, verbose_name="Configuración por integrante"
    )

    def __str__(self):
        return f"{self.public_name or self.name} ({self.name})"

    class Meta:
        verbose_name = "Plataforma con API e interacción"
        verbose_name_plural = "Plataformas con API e interacción"


class InteractionType(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    public_name = models.CharField(max_length=120, blank=True, null=True)
    way = models.CharField(max_length=5, choices=WAY_CHOICES)
    # is_attachment = models.BooleanField(default=False)
    group_type = models.CharField(
        max_length=20, choices=GROUP_TYPES, blank=True, null=True
    )
    # description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tipo de interacción'
        verbose_name_plural = 'Tipos de interacción'


class ApiRecord(models.Model):
    """
    IN this model (ApiRecord) we save all the calls (incoming and outgoing)
    from the API of third party platforms
    """
    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE
    )
    body = JSONField()
    interaction_type = models.ForeignKey(
        InteractionType, on_delete=models.CASCADE
    )
    is_incoming = models.BooleanField(default=True)
    response_status = models.SmallIntegerField(blank=True, null=True)
    response_body = JSONField(blank=True, null=True)
    repeated = models.ForeignKey(
        'self', on_delete=models.CASCADE, blank=True, null=True
    )
    error_text = models.TextField(blank=True, null=True)
    errors = JSONField(blank=True, null=True)
    success = models.BooleanField(default=False)
    created = models.DateTimeField(blank=True, null=True)
    datetime = models.IntegerField(blank=True, null=True)

    def add_errors(self, errors: list, e: Optional[BaseException] = None) -> None:
        if not errors:
            return

        if not self.errors:
            self.errors = []
        self.errors += errors  # type: ignore

    def add_error(self, error: dict, e: Optional[BaseException] = None) -> None:
        if not self.errors:
            self.errors = []

        if e:
            error["error"] = str(e)
            error["traceback"] = traceback.format_exc()
        self.errors.append(error)  # type: ignore

    def save(self, *args, **kwargs):
        if self.errors:
            self.errors = ensure_json_compatible(self.errors)
        return super().save(*args, **kwargs)

    def __del__(self):
        if not getattr(self, "pk", None):
            return
        self.success = not self.errors
        if self.errors:
            print("Error in API record: ")
            pprint(self.errors)

        self.save()
