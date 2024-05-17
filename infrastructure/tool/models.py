from django.db import models
from django.db.models import JSONField

from infrastructure.place.models import Space
from infrastructure.service.models import InteractionType


init_collections = [
    ("basic", "Básicas", False, True, None),
    ("generic", "Genéricas", False, True, None),
    ("yks", "Yeeko", True, True, "yeeko"),
    ("desabasto", "Cero Desabasto", True, False, None),
    ("borde", "Borde Político", True, False, "borde"),
]

init_behaviors = [
    ("text", "text", "generic", True, True, True, True),
    ("image", "image", "generic", True, True, True, True),
]

DATA_TYPES = (
    ('integer', 'Número'),
    ('string', 'Texto'),
    ('boolean', 'Booleano'),
    ('json', 'JSON'),
    ('any', 'Cualquiera'),
    ('foreign_key', 'Llave Foránea'),
)

MODELS = (
    ('piece', 'Piece'),
    ('fragment', 'Fragment'),
    ('yeekonsult', 'Yeeko'),
    ('reply', 'Reply'),
)


class Collection(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    public_name = models.CharField(max_length=80, blank=True, null=True)
    is_custom = models.BooleanField(default=False)
    open_available = models.BooleanField(default=True)
    spaces = models.ManyToManyField(Space, blank=True)
    app_label = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Colección'
        verbose_name_plural = 'Colecciones'


class Behavior(models.Model):
    name = models.CharField(max_length=80, primary_key=True)
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, blank=True, null=True
    )
    can_piece = models.BooleanField(default=True)
    can_destination = models.BooleanField(default=True)
    in_code = models.BooleanField(default=False)

    # Esto es opcional, solo para casos muy específicos
    interaction_type = models.ForeignKey(
        InteractionType, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Función'
        verbose_name_plural = 'Funciones'


class Parameter(models.Model):
    behavior = models.ForeignKey(Behavior, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    public_name = models.CharField(max_length=80, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)
    # RICK 5: Aún no decido si quiero mantener esto:
    default_value = models.CharField(max_length=255, blank=True, null=True)
    data_type = models.CharField(max_length=20, choices=DATA_TYPES)
    customizable_by_piece = models.BooleanField(default=False)
    addl_config = JSONField(blank=True, null=True)
    rules = JSONField(blank=True, null=True)
    model = models.CharField(
        max_length=20, choices=MODELS, blank=True, null=True)
    order = models.IntegerField(default=40)
    addl_dashboard = JSONField(blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Parámetro'
        verbose_name_plural = 'Parámetros'
        ordering = ['order']
