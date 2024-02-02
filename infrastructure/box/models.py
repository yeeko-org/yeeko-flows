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


class Written(models.Model):
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


class Piece(models.Model):
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

    def __str__(self):
        return f"{self.name} ({self.crate.name})"

    class Meta:
        verbose_name = 'Pieza (Mensaje)'
        verbose_name_plural = 'Piezas (Mensajes)'
        ordering = ['order_in_crate']


class Fragment(models.Model):
    piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, related_name='fragments')
    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(
        max_length=255, verbose_name='Título', blank=True, null=True)
    subtitle = models.CharField(
        max_length=255, verbose_name='Subtítulo', blank=True, null=True)
    text = models.TextField(
        verbose_name='Texto', blank=True, null=True)
    header = models.CharField(
        max_length=255, verbose_name='Encabezado', blank=True, null=True)
    footer = models.CharField(
        max_length=255, verbose_name='Pie de página', blank=True, null=True)
    file = models.FileField(
        upload_to='box', blank=True, null=True,
        verbose_name='Archivo o imagen')
    media_url = models.CharField(
        max_length=255, verbose_name='URL de multimedia', blank=True, null=True)
    addl_params = JSONField(blank=True, null=True)
    media_type = models.CharField(
        max_length=20, choices=MEDIA_TYPES, blank=True, null=True)
    destination_header = models.ForeignKey(
        "Destination", on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Encabezado del destino', related_name='headers')
    embedded_piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Pieza embebida')
    order = models.SmallIntegerField(default=0)
    reply_title = models.CharField(
        max_length=80, verbose_name='Título de botón de respuesta',
        blank=True, null=True)
    deleted = models.BooleanField(
        default=False, verbose_name='Borrado')

    def __str__(self):
        return f"{self.piece.name} - {self.title}"

    class Meta:
        verbose_name = 'Fragmento'
        verbose_name_plural = 'Fragmentos'
        ordering = ['order']


class Reply(models.Model):
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
        return f"{self.fragment.title} - {self.title}"

    class Meta:
        verbose_name = 'Respuesta (Botón)'
        verbose_name_plural = 'Respuestas (Botones)'
        ordering = ['order']


class MessageLink(models.Model):
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


class Destination(models.Model):
    DESTINATION_TYPES = (
        ('url', 'URL'),
        ('behavior', 'Función Behavior'),
        ('piece', 'Pieza'),
    )

    destination_type = models.CharField(
        max_length=20, choices=DESTINATION_TYPES,
        verbose_name='Tipo de destino')
    piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        related_name='default_destinations')
    piece_dest = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        related_name='origins')
    behavior = models.ForeignKey(
        Behavior, on_delete=models.CASCADE, blank=True, null=True,
        related_name='destinations')
    reply = models.ForeignKey(
        Reply, on_delete=models.CASCADE, blank=True, null=True,
        related_name='destinations')
    written = models.ForeignKey(
        Written, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Opción escrita', related_name='destinations')
    message_link = models.ForeignKey(
        MessageLink, on_delete=models.CASCADE, blank=True, null=True,
        verbose_name='Link con mensaje', related_name='destinations')
    addl_params = JSONField(blank=True, null=True)
    url = models.CharField(
        max_length=255, verbose_name='URL', blank=True, null=True)
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
