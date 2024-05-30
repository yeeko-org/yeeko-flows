from django.db import models
from django.db.models import JSONField


from infrastructure.flow.models import Crate
from infrastructure.tool.models import Behavior, Collection
from infrastructure.xtra.models import Extra
from infrastructure.place.models import Account

MEDIA_TYPES = (
    ('image', 'Imagen'),
    ('video', 'Video'),
    ('audio', 'Audio'),
    ('file', 'Archivo'),
    ('sticker', 'Sticker'),
)


class AssingMixin:
    def __init__(self, *args, **kwargs) -> None:
        from infrastructure.assign.models import Assign
        self.assignments: models.QuerySet[Assign]
        super().__init__(*args, **kwargs)

    def set_assign(self, member, interaction):
        for assing in self.assignments.filter(deleted=False):
            assing.to_member(member, interaction)


class DestinationMixin:
    destinations: models.QuerySet["Destination"]

    def get_destinations(self):
        return self.destinations.filter(deleted=False)


class Written(models.Model, AssingMixin, DestinationMixin):
    extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE,
        blank=True, null=True)
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE,
        blank=True, null=True)
    available = models.BooleanField(
        default=False, verbose_name='Disponible')

    def __str__(self):
        return self.extra.name if self.extra else str(self.pk)

    class Meta:
        verbose_name = 'Opción escrita'
        verbose_name_plural = 'Opciones escritas'


class Piece(models.Model, AssingMixin, DestinationMixin):
    crate = models.ForeignKey(
        Crate, on_delete=models.CASCADE, related_name='pieces')
    name = models.CharField(
        max_length=80, verbose_name='Nombre')
    description = models.TextField(
        verbose_name='Descripción')
    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE,
        blank=True, null=True)
    default_extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE,
        blank=True, null=True)
    insistent = models.BooleanField(
        default=False, verbose_name='Insistente')
    mandatory = models.BooleanField(
        default=False, verbose_name='Obligatorio')
    config = JSONField(blank=True, null=True, default=dict)
    written = models.OneToOneField(
        Written, on_delete=models.CASCADE,
        blank=True, null=True, verbose_name='Opción escrita')
    order_in_crate = models.SmallIntegerField(blank=True, null=True)
    deleted = models.BooleanField(
        default=False, verbose_name='Borrado')

    fragments: models.QuerySet["Fragment"]

    def __str__(self):
        return f"{self.name} ({self.crate.name})"

    class Meta:
        verbose_name = 'Pieza (Mensaje)'
        verbose_name_plural = 'Piezas (Mensajes)'
        ordering = ['order_in_crate']


class Fragment(models.Model):
    FRAGMENT_TYPES = (
        ("message", "Mensaje"),
        ("behavior", "Función Behavior"),
        ("embedded", "Pieza embebida"),
    )
    fragment_type = models.CharField(
        max_length=20, choices=FRAGMENT_TYPES, blank=True, null=True
    )
    piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, related_name='fragments')
    order = models.SmallIntegerField(default=0)

    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE, blank=True, null=True)
    addl_params = JSONField(blank=True, null=True)
    deleted = models.BooleanField(
        default=False, verbose_name='Borrado')

    file = models.FileField(
        upload_to='box', blank=True, null=True,
        verbose_name='Archivo o imagen')
    media_url = models.CharField(
        max_length=255, verbose_name='URL de multimedia', blank=True, null=True)
    media_type = models.CharField(
        max_length=20, choices=MEDIA_TYPES, blank=True, null=True)

    header = models.CharField(
        max_length=255, verbose_name='Encabezado', blank=True, null=True)
    body = models.TextField(
        verbose_name='Texto', blank=True, null=True)
    footer = models.CharField(
        max_length=255, verbose_name='Pie de página', blank=True, null=True)
    reply_title = models.CharField(
        max_length=80, verbose_name='Título de botón de respuesta',
        blank=True, null=True)

    embedded_piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Pieza embebida')

    replies: models.QuerySet["Reply"]

    def __str__(self):
        if self.fragment_type == 'message':
            return f"{self.piece.name} - {self.body}"
        elif self.fragment_type == 'behavior' and self.behavior:
            return f"{self.piece.name} - {self.behavior.name}"
        elif self.fragment_type == 'embedded' and self.embedded_piece:
            return f"{self.piece.name} - {self.embedded_piece.name}"
        return f"{self.piece.name} - {self.pk}"

    class Meta:
        verbose_name = 'Fragmento'
        verbose_name_plural = 'Fragmentos'
        ordering = ['order']


class Reply(models.Model, AssingMixin, DestinationMixin):
    fragment = models.ForeignKey(
        Fragment, on_delete=models.CASCADE, related_name='replies')
    destination = models.ForeignKey(
        "Destination", on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Destino', related_name='replies')
    title = models.CharField(
        max_length=255, verbose_name='text', blank=True, null=True)
    description = models.CharField(
        max_length=255, verbose_name='Descripción', blank=True, null=True)
    large_title = models.CharField(
        max_length=255, verbose_name='Título grande', blank=True, null=True)
    addl_params = JSONField(blank=True, null=True)
    context = JSONField(
        blank=True, null=True, verbose_name='Contexto para chatGPT')
    order = models.SmallIntegerField(blank=True, null=True)
    is_jump = models.BooleanField(
        default=True, help_text='Funciona para evitar la pregunta')
    use_piece_config = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False, verbose_name='Borrado')

    def __str__(self):
        return f"{self.fragment} - {self.title}"

    class Meta:
        verbose_name = 'Respuesta (Botón)'
        verbose_name_plural = 'Respuestas (Botones)'
        ordering = ['order']


class MessageLink(models.Model, DestinationMixin):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    link = models.URLField(max_length=255, blank=True, null=True)
    message = models.CharField(max_length=140, blank=True, null=True)
    qr_code_png = models.ImageField(
        upload_to='qr_codes', blank=True, null=True)
    qr_code_svg = models.ImageField(
        upload_to='qr_codes', blank=True, null=True)

    def __str__(self):
        return f"{self.account} - {self.message}"

    class Meta:
        verbose_name_plural = "Message Links"
        verbose_name = "Message Link"


class Destination(models.Model, AssingMixin):
    DESTINATION_TYPES = (
        ('url', 'URL'),
        ('behavior', 'Función Behavior'),
        ('piece', 'Pieza'),
    )
    # --------------------------------origin--------------------------------
    reply = models.ForeignKey(
        Reply, on_delete=models.CASCADE, blank=True, null=True,
        related_name='destinations')
    written = models.ForeignKey(
        Written, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Opción escrita', related_name='destinations')
    piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        related_name='destinations')
    message_link = models.ForeignKey(
        MessageLink, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Link con mensaje', related_name='destinations')
    # ------------------------------end origin------------------------------

    # -------------------------------destination----------------------------
    destination_type = models.CharField(
        max_length=20, choices=DESTINATION_TYPES,
        verbose_name='Tipo de destino')
    piece_dest = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        related_name='origins')
    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE, blank=True, null=True,
        related_name='destinations')
    url = models.CharField(
        max_length=255, verbose_name='URL', blank=True, null=True)
    # -----------------------------end destination--------------------------

    addl_params = JSONField(blank=True, null=True)
    is_default = models.BooleanField(default=True)
    order = models.SmallIntegerField(blank=True, null=True)
    deleted = models.BooleanField(default=False, verbose_name='Borrado')

    def __str__(self):
        name = self.piece.name if self.piece else self.pk
        return f"{name} - {self.destination_type}"

    class Meta:
        verbose_name = 'Destino'
        verbose_name_plural = 'Destinos'
        ordering = ['order']
